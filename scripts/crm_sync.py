#!/usr/bin/env python3
"""
CRM Sync — Bitrix24 → Airtable
Chạy mỗi 5 phút. Hai nhiệm vụ:

A. Lead mới (STATUS=NEW):
   → Convert thành Deal, STAGE = C1:PREPARATION (Liên lạc lại sau)
   → Lưu Airtable, Telegram thông báo

B. Follow-up tự động (sau 10-15 phút):
   → Tìm Deal trong Airtable đang "Liên lạc Lại Sau" đã > 12 phút
   → Chuyển Bitrix24 sang C1:EXECUTING (Khách Đã Nhận Thông Tin)
   → Cập nhật Airtable, Telegram thông báo
"""

import sys
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent


def load_env():
    import os
    env = {}
    env_file = WORKSPACE / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    env.update({k: v for k, v in os.environ.items() if v})
    return env


ENV = load_env()

BITRIX_URL    = ENV.get("BITRIX24_WEBHOOK_URL", "").rstrip("/")
AIRTABLE_KEY  = ENV.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE = ENV.get("AIRTABLE_BASE_ID", "")
TG_TOKEN      = ENV.get("TELEGRAM_CRM_BOT_TOKEN", "")
TG_CHAT       = ENV.get("TELEGRAM_CHAT_ID", "")

LEADS_TABLE = "tblJxEmk2yy6FwfJQ"
AT_HEADERS  = {"Authorization": f"Bearer {AIRTABLE_KEY}", "Content-Type": "application/json"}
AT_URL      = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{LEADS_TABLE}"

# Sau bao nhiêu phút kể từ lúc tạo record thì tự động chuyển sang "Đã Nhận Thông Tin"
AUTO_ADVANCE_AFTER_MIN = 12

# Bitrix24 Deal STAGE_ID → Airtable Giai đoạn
STAGE_MAP = {
    "C1:NEW":                "Tiếp nhận & Phân phối",
    "C1:UC_MH417S":          "Data Import",
    "C1:PREPARATION":        "Liên lạc Lại Sau",
    "C1:PREPAYMENT_INVOICE": "Máy Bận / Chưa Nghe",
    "C1:UC_VN46PT":          "Không Quan Tâm",
    "C1:EXECUTING":          "Đã Nhận Thông Tin",
    "C1:UC_W398X1":          "Quan Tâm",
    "C1:UC_AIHMUN":          "Tham Quan Dự Án",
    "C1:UC_301T7U":          "Tham Gia Sự Kiện",
    "C1:FINAL_INVOICE":      "Cần PIC Xác Nhận",
    "C1:UC_4JVPKB":          "Đã Booking",
    "C1:WON":                "Giao Dịch Thành Công",
    "C1:LOSE":               "Chê Giá / Tài Chính Yếu",
    "C1:UC_3GKFB3":          "Môi Giới",
    "C1:UC_1E1LLX":          "Dự Án Khác",
    "C1:UC_WJK06W":          "Sai Thông Tin",
    "C1:UC_HVVPK7":          "Huỷ Cọc",
    "C1:UC_6E1UDR":          "Rác",
    "C1:UC_22GJPC":          "Data Thu Hồi",
    "C1:UC_30RM6I":          "Lưu Trữ",
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


# ─── Helpers ──────────────────────────────────────────────────────────────────

def parse_source(source_id):
    s = str(source_id)
    nguon = SOURCE_MAP.get(s)
    if not nguon:
        prefix = s.split("|")[0] if "|" in s else s
        nguon = SOURCE_MAP.get(prefix, "Khác")
    return nguon


def telegram(text):
    if not TG_TOKEN or not TG_CHAT:
        return
    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id": TG_CHAT, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )


# ─── Bitrix24 ─────────────────────────────────────────────────────────────────

def get_new_leads(since_minutes=8):
    """Lấy leads STATUS=NEW tạo trong vòng since_minutes phút qua."""
    tz_vn = timezone(timedelta(hours=7))
    since = datetime.now(tz_vn) - timedelta(minutes=since_minutes)
    since_str = since.strftime("%Y-%m-%dT%H:%M:%S")

    all_leads, start = [], 0
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
            print(f"  ❌ Bitrix24 lead.list {r.status_code}: {r.text[:200]}")
            break
        data = r.json()
        batch = data.get("result", [])
        all_leads.extend(batch)
        next_offset = data.get("next")
        if not next_offset or not batch:
            break
        start = next_offset
    return all_leads


def convert_lead_to_deal(lead):
    """
    Convert lead → Deal STAGE=C1:PREPARATION (Liên lạc lại sau).
    Trả về deal_id (int) hoặc None.
    """
    name_parts = [lead.get("NAME", ""), lead.get("LAST_NAME", "")]
    name = " ".join(p for p in name_parts if p).strip() or lead.get("TITLE", "Lead")
    phone_raw = lead.get("PHONE", []) or []
    phone = phone_raw[0]["VALUE"] if phone_raw else ""

    deal_fields = {
        "STAGE_ID": "C1:PREPARATION",
        "TITLE":    f"[Lead] {name}" + (f" — {phone}" if phone else ""),
    }
    if lead.get("ASSIGNED_BY_ID"):
        deal_fields["ASSIGNED_BY_ID"] = lead["ASSIGNED_BY_ID"]

    r = requests.post(
        f"{BITRIX_URL}/crm.lead.convert.json",
        json={"ID": int(lead["ID"]), "FIELDS": {"DEAL": deal_fields}},
        timeout=15,
    )
    if r.status_code != 200:
        print(f"  ⚠️  convert HTTP {r.status_code}: {r.text[:200]}")
        return None

    result = r.json().get("result", {})
    deal = result.get("DEAL", {})
    deal_id = deal.get("ID") if isinstance(deal, dict) else None

    if deal_id:
        return int(deal_id)

    # Fallback: chỉ update Lead STATUS tránh bị chuyển người
    print(f"  ⚠️  Convert không tạo Deal — fallback IN_PROCESS")
    requests.post(
        f"{BITRIX_URL}/crm.lead.update.json",
        json={"id": int(lead["ID"]), "FIELDS": {"STATUS_ID": "IN_PROCESS"}},
        timeout=15,
    )
    return None


def advance_deal_stage(deal_id, stage_id):
    """Update stage của Deal trong Bitrix24. Trả về True nếu thành công."""
    r = requests.post(
        f"{BITRIX_URL}/crm.deal.update.json",
        json={"id": int(deal_id), "FIELDS": {"STAGE_ID": stage_id}},
        timeout=15,
    )
    if r.status_code == 200 and r.json().get("result") is True:
        return True
    print(f"  ⚠️  deal.update #{deal_id} → {stage_id}: {r.text[:200]}")
    return False


# ─── Airtable ─────────────────────────────────────────────────────────────────

def get_synced_lead_ids():
    ids = set()
    offset = None
    while True:
        params = {"fields[]": "ID Bitrix24", "pageSize": 100}
        if offset:
            params["offset"] = offset
        r = requests.get(AT_URL, headers=AT_HEADERS, params=params, timeout=15)
        if r.status_code != 200:
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


def get_pending_advance():
    """
    Trả về list records đang Giai đoạn='Liên lạc Lại Sau' và đã tạo >= AUTO_ADVANCE_AFTER_MIN phút.
    Dùng Airtable filterByFormula với CREATED_TIME().
    """
    formula = (
        f'AND({{Giai đoạn}}="Liên lạc Lại Sau",'
        f'IS_BEFORE(CREATED_TIME(),DATEADD(NOW(),{-AUTO_ADVANCE_AFTER_MIN},"minutes")))'
    )
    params = {
        "filterByFormula": formula,
        "fields[]": ["Tên / Nick name", "Số điện thoại", "ID Bitrix24", "ID Deal Bitrix24"],
        "pageSize": 50,
    }
    r = requests.get(AT_URL, headers=AT_HEADERS, params=params, timeout=15)
    if r.status_code != 200:
        print(f"  ⚠️  Airtable pending query: {r.text[:200]}")
        return []
    return r.json().get("records", [])


def create_record(fields):
    r = requests.post(
        AT_URL,
        headers=AT_HEADERS,
        json={"records": [{"fields": fields}], "typecast": True},
        timeout=15,
    )
    if r.status_code in (200, 201):
        return r.json()["records"][0]["id"]
    print(f"  ❌ Airtable create: {r.text[:300]}")
    return None


def update_record(record_id, fields):
    r = requests.patch(
        f"{AT_URL}/{record_id}",
        headers=AT_HEADERS,
        json={"fields": fields, "typecast": True},
        timeout=15,
    )
    return r.status_code in (200, 201)


def build_lead_fields(lead, deal_id=None):
    name_parts = [lead.get("NAME", ""), lead.get("LAST_NAME", "")]
    name = " ".join(p for p in name_parts if p).strip() or lead.get("TITLE", "Lead")
    phone_raw = lead.get("PHONE", []) or []
    phone = phone_raw[0]["VALUE"] if phone_raw else ""
    email_raw = lead.get("EMAIL", []) or []
    email = email_raw[0]["VALUE"] if email_raw else ""
    nguon = parse_source(lead.get("SOURCE_ID", ""))

    fields = {
        "Tên / Nick name":     name,
        "ID Bitrix24":         str(lead["ID"]),
        "Giai đoạn":           "Liên lạc Lại Sau",
        "Nguồn lead":          nguon,
        "Yêu cầu khách hàng": lead.get("COMMENTS", "") or "",
    }
    if phone:
        fields["Số điện thoại"] = phone
    if email:
        fields["Email"] = email
    if lead.get("DATE_CREATE"):
        fields["Thời gian lead đổ về"] = lead["DATE_CREATE"]
    if deal_id:
        fields["ID Deal Bitrix24"] = str(deal_id)
        fields["Ghi chú chăm sóc"] = (
            f"Deal: https://iqi.bitrix24.vn/crm/deal/details/{deal_id}/"
        )
    return fields


# ─── Telegram notifications ───────────────────────────────────────────────────

def notify_new_lead(lead, at_id, deal_id):
    name_parts = [lead.get("NAME", ""), lead.get("LAST_NAME", "")]
    name = " ".join(p for p in name_parts if p).strip() or lead.get("TITLE", "Lead")
    phone_raw = lead.get("PHONE", []) or []
    phone = phone_raw[0]["VALUE"] if phone_raw else "—"
    comments = (lead.get("COMMENTS", "") or "").strip()
    if len(comments) > 200:
        comments = comments[:200] + "…"
    nguon = parse_source(lead.get("SOURCE_ID", ""))

    at_link = f"https://airtable.com/{AIRTABLE_BASE}/{LEADS_TABLE}/{at_id}"
    if deal_id:
        bx_link = f"https://iqi.bitrix24.vn/crm/deal/details/{deal_id}/"
        bx_label = f"Deal #{deal_id}"
        stage_line = "✅ Bitrix24: <b>Liên lạc lại sau</b>"
    else:
        bx_link = f"https://iqi.bitrix24.vn/crm/lead/details/{lead['ID']}/"
        bx_label = f"Lead #{lead['ID']}"
        stage_line = "⚠️ Cần xử lý thủ công trên Bitrix24"

    msg = (
        f"🔔 <b>Lead mới!</b>\n\n"
        f"👤 <b>{name}</b>\n"
        f"📞 {phone}\n"
        f"📣 Nguồn: {nguon}\n"
    )
    if comments:
        msg += f"💬 {comments}\n"
    msg += (
        f"\n{stage_line}\n"
        f"⏱ Tự động chuyển sang <b>Khách Đã Nhận Thông Tin</b> sau {AUTO_ADVANCE_AFTER_MIN} phút\n\n"
        f"<a href='{bx_link}'>🗂 {bx_label}</a>  |  <a href='{at_link}'>📋 Airtable</a>"
    )
    telegram(msg)


def notify_advanced(name, phone, deal_id, at_id):
    at_link = f"https://airtable.com/{AIRTABLE_BASE}/{LEADS_TABLE}/{at_id}"
    if deal_id:
        bx_link = f"https://iqi.bitrix24.vn/crm/deal/details/{deal_id}/"
        bx_label = f"Deal #{deal_id}"
    else:
        bx_link = ""
        bx_label = ""

    msg = (
        f"📋 <b>Đã chuyển giai đoạn</b>\n\n"
        f"👤 <b>{name}</b>  📞 {phone or '—'}\n\n"
        f"Liên lạc lại sau → <b>Khách Đã Nhận Thông Tin</b>\n\n"
    )
    links = [f"<a href='{at_link}'>📋 Airtable</a>"]
    if bx_link:
        links.insert(0, f"<a href='{bx_link}'>🗂 {bx_label}</a>")
    msg += "  |  ".join(links)
    telegram(msg)


# ─── Task A: sync new leads ────────────────────────────────────────────────────

def sync_new_leads():
    leads = get_new_leads(since_minutes=8)
    print(f"  [A] Bitrix24 new leads (STATUS=NEW, 8 phút): {len(leads)}")
    if not leads:
        return

    synced = get_synced_lead_ids()

    for lead in leads:
        lead_id = str(lead["ID"])
        if lead_id in synced:
            continue

        name_parts = [lead.get("NAME", ""), lead.get("LAST_NAME", "")]
        name = " ".join(p for p in name_parts if p).strip() or lead.get("TITLE", "Lead")
        print(f"  → Lead #{lead_id}: {name}")

        # Convert lead → Deal C1:PREPARATION
        deal_id = convert_lead_to_deal(lead)
        print(f"     Bitrix24 Deal: #{deal_id}" if deal_id else "     ⚠️  Không tạo được Deal")

        # Airtable record
        fields = build_lead_fields(lead, deal_id=deal_id)
        at_id = create_record(fields)
        if not at_id:
            continue

        # Telegram
        notify_new_lead(lead, at_id, deal_id)
        print(f"     ✅ Airtable {at_id} | Telegram sent")


# ─── Task B: auto-advance after 12 min ────────────────────────────────────────

def auto_advance_deals():
    pending = get_pending_advance()
    print(f"  [B] Pending auto-advance: {len(pending)}")

    for rec in pending:
        rec_id = rec["id"]
        f = rec.get("fields", {})
        name    = f.get("Tên / Nick name", "—")
        phone   = f.get("Số điện thoại", "")
        deal_id = f.get("ID Deal Bitrix24", "")

        print(f"  → Advance: {name} (Deal #{deal_id or 'N/A'})")

        # Update Bitrix24 deal stage
        bitrix_ok = False
        if deal_id:
            bitrix_ok = advance_deal_stage(deal_id, "C1:EXECUTING")
            status = "✅ Bitrix24 → C1:EXECUTING" if bitrix_ok else "⚠️  Bitrix24 update thất bại"
            print(f"     {status}")

        # Update Airtable stage
        at_ok = update_record(rec_id, {"Giai đoạn": "Đã Nhận Thông Tin"})
        print(f"     Airtable: {'✅' if at_ok else '❌'}")

        # Telegram
        notify_advanced(name, phone, deal_id, rec_id)
        print(f"     Telegram sent")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not BITRIX_URL:
        print("❌ BITRIX24_WEBHOOK_URL chưa có trong .env")
        sys.exit(1)
    if not AIRTABLE_KEY or not AIRTABLE_BASE:
        print("❌ AIRTABLE_API_KEY hoặc AIRTABLE_BASE_ID chưa có")
        sys.exit(1)

    now = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
    print(f"🔄 CRM Sync — {now} (ICT)")

    sync_new_leads()
    auto_advance_deals()

    print("✅ Done")


if __name__ == "__main__":
    main()
