#!/usr/bin/env python3
"""
CRM Sync — Bitrix24 → Airtable
Polls Bitrix24 mỗi 5 phút. Khi phát hiện lead mới (STATUS=NEW):
  1. Convert lead → Deal với STAGE_ID=C1:NEW (Tiếp nhận & Phân phối Lead)
  2. Tạo record Airtable giai đoạn "Tiếp nhận & Phân phối"
  3. Telegram thông báo kèm link Deal + link Airtable
"""

import sys
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent


def load_env():
    env = {}
    env_file = WORKSPACE / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


ENV = load_env()

BITRIX_URL    = ENV.get("BITRIX24_WEBHOOK_URL", "").rstrip("/")
AIRTABLE_KEY  = ENV.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE = ENV.get("AIRTABLE_BASE_ID", "")
TG_TOKEN      = ENV.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT       = ENV.get("TELEGRAM_CHAT_ID", "")

LEADS_TABLE = "tblJxEmk2yy6FwfJQ"
AT_HEADERS  = {"Authorization": f"Bearer {AIRTABLE_KEY}", "Content-Type": "application/json"}
AT_URL      = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{LEADS_TABLE}"

# Bitrix24 Deal STAGE_ID → Airtable Giai đoạn
STAGE_MAP = {
    "C1:NEW":              "Tiếp nhận & Phân phối",
    "C1:UC_MH417S":        "Data Import",
    "C1:PREPARATION":      "Liên lạc Lại Sau",
    "C1:PREPAYMENT_INVOICE": "Máy Bận / Chưa Nghe",
    "C1:UC_VN46PT":        "Không Quan Tâm",
    "C1:EXECUTING":        "Đã Nhận Thông Tin",
    "C1:UC_W398X1":        "Quan Tâm",
    "C1:UC_AIHMUN":        "Tham Quan Dự Án",
    "C1:UC_301T7U":        "Tham Gia Sự Kiện",
    "C1:FINAL_INVOICE":    "Cần PIC Xác Nhận",
    "C1:UC_4JVPKB":        "Đã Booking",
    "C1:WON":              "Giao Dịch Thành Công",
    "C1:LOSE":             "Chê Giá / Tài Chính Yếu",
    "C1:UC_3GKFB3":        "Môi Giới",
    "C1:UC_1E1LLX":        "Dự Án Khác",
    "C1:UC_WJK06W":        "Sai Thông Tin",
    "C1:UC_HVVPK7":        "Huỷ Cọc",
    "C1:UC_6E1UDR":        "Rác",
    "C1:UC_22GJPC":        "Data Thu Hồi",
    "C1:UC_30RM6I":        "Lưu Trữ",
}

# Bitrix24 SOURCE_ID → Nguồn lead
SOURCE_MAP = {
    "ADVERTISING":    "Google Ads",
    "WEB":            "Website",
    "PARTNER":        "Giới thiệu",
    "RECOMMENDATION": "Giới thiệu",
    "UC_0CW3PH":      "TikTok Ads",
    "UC_3DH873":      "Zalo OA",
    "1":              "Facebook Ads",
    "2":              "Zalo OA",
    "3":              "Google Ads",
    "4":              "TikTok Ads",
    "5":              "Website",
    "6":              "Giới thiệu",
}


# ─── Bitrix24 ─────────────────────────────────────────────────────────────────

def get_bitrix_leads(since_minutes=8):
    tz_vn = timezone(timedelta(hours=7))
    since = datetime.now(tz_vn) - timedelta(minutes=since_minutes)
    since_str = since.strftime("%Y-%m-%dT%H:%M:%S")

    all_leads = []
    start = 0
    while True:
        params = {
            "FILTER[>=DATE_CREATE]": since_str,
            "FILTER[STATUS_ID]":     "NEW",
            "SELECT[]": ["ID", "TITLE", "NAME", "LAST_NAME", "PHONE", "EMAIL",
                         "SOURCE_ID", "STATUS_ID", "DATE_CREATE", "COMMENTS", "ASSIGNED_BY_ID"],
            "ORDER[DATE_CREATE]": "ASC",
            "start": start,
        }
        r = requests.get(f"{BITRIX_URL}/crm.lead.list.json", params=params, timeout=15)
        if r.status_code != 200:
            print(f"  ❌ Bitrix24 {r.status_code}: {r.text[:200]}")
            break
        data = r.json()
        batch = data.get("result", [])
        all_leads.extend(batch)
        next_offset = data.get("next")
        if not next_offset or len(batch) == 0:
            break
        start = next_offset
    return all_leads


def convert_lead_to_deal(lead):
    """
    Convert lead → Deal với STAGE_ID=C1:NEW (Tiếp nhận & Phân phối Lead).
    Trả về deal_id (int) nếu thành công, None nếu thất bại.
    """
    name_parts = [lead.get("NAME", ""), lead.get("LAST_NAME", "")]
    name = " ".join(p for p in name_parts if p).strip() or lead.get("TITLE", "Lead")

    phone_raw = lead.get("PHONE", []) or []
    phone = phone_raw[0]["VALUE"] if phone_raw else ""

    deal_fields = {
        "STAGE_ID": "C1:NEW",
        "TITLE":    f"[Lead] {name}" + (f" — {phone}" if phone else ""),
    }
    if lead.get("ASSIGNED_BY_ID"):
        deal_fields["ASSIGNED_BY_ID"] = lead["ASSIGNED_BY_ID"]

    payload = {
        "ID":     int(lead["ID"]),
        "FIELDS": {"DEAL": deal_fields},
    }

    r = requests.post(f"{BITRIX_URL}/crm.lead.convert.json", json=payload, timeout=15)
    if r.status_code != 200:
        print(f"  ⚠️  Convert failed (HTTP {r.status_code}): {r.text[:200]}")
        return None

    data = r.json()
    result = data.get("result", {})

    # Kết quả trả về: {"DEAL": {"ID": 123}, ...}
    deal = result.get("DEAL", {})
    deal_id = deal.get("ID") if isinstance(deal, dict) else None

    if deal_id:
        return int(deal_id)

    # Nếu convert fail → fallback: update lead STATUS_ID=IN_PROCESS để giữ lead
    print(f"  ⚠️  Convert không tạo được Deal — fallback update Lead STATUS=IN_PROCESS")
    r2 = requests.post(
        f"{BITRIX_URL}/crm.lead.update.json",
        json={"id": int(lead["ID"]), "FIELDS": {"STATUS_ID": "IN_PROCESS"}},
        timeout=15,
    )
    if r2.status_code == 200 and r2.json().get("result") is True:
        print(f"  ✅ Lead #{lead['ID']} STATUS → IN_PROCESS (fallback)")
    else:
        print(f"  ❌ Fallback update cũng thất bại: {r2.text[:150]}")
    return None


# ─── Airtable ─────────────────────────────────────────────────────────────────

def get_synced_ids():
    """Trả về set tất cả ID Bitrix24 (Lead ID) đã có trong Airtable."""
    ids = set()
    offset = None
    while True:
        params = {"fields[]": "ID Bitrix24", "pageSize": 100}
        if offset:
            params["offset"] = offset
        r = requests.get(AT_URL, headers=AT_HEADERS, params=params, timeout=15)
        if r.status_code != 200:
            print(f"  ⚠️  Không đọc được Airtable: {r.text[:200]}")
            break
        data = r.json()
        for rec in data.get("records", []):
            bid = rec.get("fields", {}).get("ID Bitrix24", "")
            if bid:
                ids.add(str(bid))
        offset = data.get("offset")
        if not offset:
            break
    return ids


def lead_to_fields(lead, deal_id=None):
    name_parts = [lead.get("NAME", ""), lead.get("LAST_NAME", "")]
    name = " ".join(p for p in name_parts if p).strip() or lead.get("TITLE", "Lead")

    phone_raw = lead.get("PHONE", []) or []
    phone = phone_raw[0]["VALUE"] if phone_raw else ""

    email_raw = lead.get("EMAIL", []) or []
    email = email_raw[0]["VALUE"] if email_raw else ""

    source_id = str(lead.get("SOURCE_ID", ""))
    nguon = SOURCE_MAP.get(source_id)
    if not nguon:
        prefix = source_id.split("|")[0] if "|" in source_id else source_id
        nguon = SOURCE_MAP.get(prefix, "Khác")

    giai_doan = "Tiếp nhận & Phân phối" if deal_id else "Mới Nhận"

    # Ghi chú: lưu link deal Bitrix24 nếu có
    ghi_chu = ""
    if deal_id:
        ghi_chu = f"Deal Bitrix24: https://iqi.bitrix24.vn/crm/deal/details/{deal_id}/"

    fields = {
        "Tên / Nick name":     name,
        "ID Bitrix24":         str(lead["ID"]),
        "Giai đoạn":           giai_doan,
        "Nguồn lead":          nguon,
        "Yêu cầu khách hàng": lead.get("COMMENTS", "") or "",
        "Ghi chú chăm sóc":   ghi_chu,
    }
    if phone:
        fields["Số điện thoại"] = phone
    if email:
        fields["Email"] = email
    if lead.get("DATE_CREATE"):
        fields["Thời gian lead đổ về"] = lead["DATE_CREATE"]
    return fields


def create_record(fields):
    r = requests.post(
        AT_URL,
        headers=AT_HEADERS,
        json={"records": [{"fields": fields}], "typecast": True},
        timeout=15,
    )
    if r.status_code in (200, 201):
        return r.json()["records"][0]["id"]
    print(f"  ❌ Airtable create failed: {r.text[:300]}")
    return None


# ─── Telegram ─────────────────────────────────────────────────────────────────

def telegram(text):
    if not TG_TOKEN or not TG_CHAT:
        return
    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id": TG_CHAT, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )


def notify_new_lead(lead, at_record_id, deal_id):
    name_parts = [lead.get("NAME", ""), lead.get("LAST_NAME", "")]
    name = " ".join(p for p in name_parts if p).strip() or lead.get("TITLE", "Lead")

    phone_raw = lead.get("PHONE", []) or []
    phone = phone_raw[0]["VALUE"] if phone_raw else "—"

    email_raw = lead.get("EMAIL", []) or []
    email = email_raw[0]["VALUE"] if email_raw else "—"

    comments = (lead.get("COMMENTS", "") or "").strip()
    if len(comments) > 250:
        comments = comments[:250] + "…"

    source_id = str(lead.get("SOURCE_ID", ""))
    nguon = SOURCE_MAP.get(source_id)
    if not nguon:
        prefix = source_id.split("|")[0] if "|" in source_id else source_id
        nguon = SOURCE_MAP.get(prefix, "Khác")

    at_link     = f"https://airtable.com/{AIRTABLE_BASE}/{LEADS_TABLE}/{at_record_id}"
    deal_link   = f"https://iqi.bitrix24.vn/crm/deal/details/{deal_id}/" if deal_id else None
    lead_link   = f"https://iqi.bitrix24.vn/crm/lead/details/{lead['ID']}/"

    if deal_id:
        status_line = f"✅ Đã vào pipeline: <b>Tiếp nhận &amp; Phân phối</b>"
    else:
        status_line = f"⚠️ Chưa tạo được Deal — cần xử lý thủ công"

    msg = (
        f"🔔 <b>Lead mới!</b>\n\n"
        f"👤 <b>{name}</b>\n"
        f"📞 {phone}\n"
        f"📧 {email}\n"
        f"📣 Nguồn: {nguon}\n"
    )
    if comments:
        msg += f"💬 {comments}\n"

    msg += f"\n{status_line}\n\n"

    links = []
    if deal_link:
        links.append(f"<a href='{deal_link}'>🗂 Deal Bitrix24</a>")
    else:
        links.append(f"<a href='{lead_link}'>🔗 Lead Bitrix24</a>")
    links.append(f"<a href='{at_link}'>📋 Airtable CRM</a>")
    msg += "  |  ".join(links)

    telegram(msg)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not BITRIX_URL:
        print("❌ BITRIX24_WEBHOOK_URL chưa có trong .env")
        sys.exit(1)
    if not AIRTABLE_KEY or not AIRTABLE_BASE:
        print("❌ AIRTABLE_API_KEY hoặc AIRTABLE_BASE_ID chưa có trong .env")
        sys.exit(1)

    now = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
    print(f"🔄 CRM Sync — {now} (ICT)")

    # 1. Lấy leads STATUS=NEW từ Bitrix24 (8 phút vừa qua)
    leads = get_bitrix_leads(since_minutes=8)
    print(f"  Bitrix24: {len(leads)} lead(s) STATUS=NEW trong 8 phút qua")

    if not leads:
        print("  Không có lead mới.")
        return

    # 2. Lấy danh sách Lead ID đã sync
    synced = get_synced_ids()
    print(f"  Airtable: {len(synced)} Lead ID đã có")

    # 3. Xử lý từng lead mới
    new_count = 0
    for lead in leads:
        lead_id = str(lead["ID"])
        if lead_id in synced:
            print(f"  ↩  Lead #{lead_id} đã có — bỏ qua")
            continue

        name_parts = [lead.get("NAME", ""), lead.get("LAST_NAME", "")]
        name = " ".join(p for p in name_parts if p).strip() or lead.get("TITLE", "Lead")
        print(f"  → Xử lý Lead #{lead_id}: {name}")

        # 3a. Convert lead → Deal C1:NEW (Tiếp nhận & Phân phối)
        deal_id = convert_lead_to_deal(lead)
        if deal_id:
            print(f"     ✅ Deal tạo thành công: #{deal_id}")
        else:
            print(f"     ⚠️  Không tạo được Deal")

        # 3b. Tạo Airtable record
        fields = lead_to_fields(lead, deal_id=deal_id)
        at_id = create_record(fields)
        if not at_id:
            continue

        new_count += 1

        # 3c. Telegram thông báo
        notify_new_lead(lead, at_id, deal_id)
        print(f"     ✅ Airtable: {at_id} | Telegram: sent")

    print(f"\n✅ Xong: {new_count} lead mới được xử lý")


if __name__ == "__main__":
    main()
