#!/usr/bin/env python3
"""
CRM Sync — Bitrix24 → Airtable
Polls Bitrix24 mỗi 5 phút. Khi phát hiện lead mới:
  1. Ngay lập tức update Bitrix24 STATUS_ID → IN_PROCESS (Tiếp nhận & Phân phối)
  2. Tạo record Airtable với giai đoạn "Đã tiếp nhận thông tin"
  3. Telegram thông báo kèm xác nhận đã chuyển trạng thái
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

# Bitrix24 SOURCE_ID → Nguồn lead (Airtable single-select)
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
            "SELECT[]": ["ID", "TITLE", "NAME", "LAST_NAME", "PHONE", "EMAIL",
                         "SOURCE_ID", "STATUS_ID", "DATE_CREATE", "COMMENTS"],
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


def accept_lead_in_bitrix(lead_id):
    """
    Chuyển STATUS_ID → IN_PROCESS (Tiếp nhận & Phân phối).
    Trả về True nếu thành công.
    """
    r = requests.post(
        f"{BITRIX_URL}/crm.lead.update.json",
        json={"id": lead_id, "FIELDS": {"STATUS_ID": "IN_PROCESS"}},
        timeout=15,
    )
    if r.status_code == 200 and r.json().get("result") is True:
        return True
    print(f"  ⚠️  Bitrix24 update lead #{lead_id}: {r.text[:200]}")
    return False


# ─── Airtable ─────────────────────────────────────────────────────────────────

def get_synced_ids():
    """Trả về set tất cả ID Bitrix24 đã có trong Airtable."""
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


def lead_to_fields(lead, accepted=False):
    """Convert Bitrix24 lead → Airtable fields dict."""
    name_parts = [lead.get("NAME", ""), lead.get("LAST_NAME", "")]
    name = " ".join(p for p in name_parts if p).strip() or lead.get("TITLE", "Lead")

    phone_raw = lead.get("PHONE", []) or []
    phone = phone_raw[0]["VALUE"] if phone_raw else ""

    email_raw = lead.get("EMAIL", []) or []
    email = email_raw[0]["VALUE"] if email_raw else ""

    source_id = str(lead.get("SOURCE_ID", ""))
    # Thử match trực tiếp, nếu không → thử tìm prefix số
    nguon = SOURCE_MAP.get(source_id)
    if not nguon:
        prefix = source_id.split("|")[0] if "|" in source_id else source_id
        nguon = SOURCE_MAP.get(prefix, "Khác")

    # Nếu đã update Bitrix24 thành công → ghi nhận đã tiếp nhận
    giai_doan = "Đã tiếp nhận thông tin" if accepted else "Mới Nhận"

    fields = {
        "Tên / Nick name":     name,
        "ID Bitrix24":         str(lead["ID"]),
        "Giai đoạn":           giai_doan,
        "Nguồn lead":          nguon,
        "Yêu cầu khách hàng": lead.get("COMMENTS", "") or "",
    }

    if phone:
        fields["Số điện thoại"] = phone
    if email:
        fields["Email"] = email

    date_create = lead.get("DATE_CREATE", "")
    if date_create:
        fields["Thời gian lead đổ về"] = date_create

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


def notify_new_lead(lead, at_record_id, accepted):
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

    at_link = f"https://airtable.com/{AIRTABLE_BASE}/{LEADS_TABLE}/{at_record_id}"
    bitrix_link = f"https://iqi.bitrix24.vn/crm/lead/details/{lead['ID']}/"

    status_line = "✅ Đã chuyển sang <b>Tiếp nhận &amp; Phân phối</b> trên Bitrix24" if accepted \
                  else "⚠️ Cần chuyển trạng thái thủ công trên Bitrix24"

    msg = (
        f"🔔 <b>Lead mới!</b>\n\n"
        f"👤 <b>{name}</b>\n"
        f"📞 {phone}\n"
        f"📧 {email}\n"
        f"📣 Nguồn: {nguon}\n"
    )
    if comments:
        msg += f"💬 {comments}\n"

    msg += (
        f"\n"
        f"{status_line}\n\n"
        f"🗂 <a href='{at_link}'>Airtable CRM</a>  |  "
        f"🔗 <a href='{bitrix_link}'>Bitrix24 #{lead['ID']}</a>"
    )

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

    # 1. Lấy leads từ Bitrix24 (8 phút vừa qua — buffer an toàn cho cronjob 5 phút)
    leads = get_bitrix_leads(since_minutes=8)
    print(f"  Bitrix24: {len(leads)} lead(s) trong 8 phút qua")

    if not leads:
        print("  Không có lead mới.")
        return

    # 2. Lấy danh sách ID đã sync để tránh duplicate
    synced = get_synced_ids()
    print(f"  Airtable: {len(synced)} Bitrix24 ID đã có")

    # 3. Xử lý từng lead mới
    new_count = 0
    for lead in leads:
        lead_id = str(lead["ID"])
        if lead_id in synced:
            print(f"  ↩  Lead #{lead_id} đã có — bỏ qua")
            continue

        name_parts = [lead.get("NAME", ""), lead.get("LAST_NAME", "")]
        name = " ".join(p for p in name_parts if p).strip() or lead.get("TITLE", "Lead")

        # 3a. Update Bitrix24 → IN_PROCESS (Tiếp nhận & Phân phối)
        accepted = accept_lead_in_bitrix(int(lead["ID"]))
        status = "✅ Bitrix24 IN_PROCESS" if accepted else "⚠️  Bitrix24 update failed"
        print(f"  {status} — Lead #{lead_id} {name}")

        # 3b. Tạo Airtable record
        fields = lead_to_fields(lead, accepted=accepted)
        at_id = create_record(fields)

        if at_id:
            new_count += 1
            # 3c. Telegram thông báo
            notify_new_lead(lead, at_id, accepted)
            print(f"  ✅ Airtable record tạo — {at_id}")

    print(f"\n✅ Xong: {new_count} lead mới được xử lý")


if __name__ == "__main__":
    main()
