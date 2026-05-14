#!/usr/bin/env python3
"""
CRM Sync — Bitrix24 → Airtable
Polls Bitrix24 for new leads (last 25 min), creates Airtable records, notifies Telegram.
Chạy bởi GitHub Actions mỗi 15 phút.
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

BITRIX_URL     = ENV.get("BITRIX24_WEBHOOK_URL", "").rstrip("/")
AIRTABLE_KEY   = ENV.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE  = ENV.get("AIRTABLE_BASE_ID", "")
TG_TOKEN       = ENV.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT        = ENV.get("TELEGRAM_CHAT_ID", "")

LEADS_TABLE = "tblJxEmk2yy6FwfJQ"
AT_HEADERS  = {"Authorization": f"Bearer {AIRTABLE_KEY}", "Content-Type": "application/json"}
AT_URL      = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{LEADS_TABLE}"

# Bitrix24 SOURCE_ID → Nguồn lead (Airtable single-select)
SOURCE_MAP = {
    "ADVERTISING": "Google Ads",
    "WEB":         "Website",
    "PARTNER":     "Giới thiệu",
    "RECOMMENDATION": "Giới thiệu",
    "1":           "Facebook Ads",
    "2":           "Zalo OA",
    "3":           "Google Ads",
    "4":           "TikTok Ads",
    "5":           "Website",
    "6":           "Giới thiệu",
}


# ─── Bitrix24 ─────────────────────────────────────────────────────────────────

def get_bitrix_leads(since_minutes=25):
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


def lead_to_fields(lead):
    """Convert Bitrix24 lead → Airtable fields dict."""
    name_parts = [lead.get("NAME", ""), lead.get("LAST_NAME", "")]
    name = " ".join(p for p in name_parts if p).strip() or lead.get("TITLE", "Lead")

    phone_raw = lead.get("PHONE", []) or []
    phone = phone_raw[0]["VALUE"] if phone_raw else ""

    email_raw = lead.get("EMAIL", []) or []
    email = email_raw[0]["VALUE"] if email_raw else ""

    source_id = str(lead.get("SOURCE_ID", ""))
    nguon = SOURCE_MAP.get(source_id, "Khác")

    fields = {
        "Tên / Nick name":       name,
        "ID Bitrix24":           str(lead["ID"]),
        "Giai đoạn":             "Mới Nhận",
        "Nguồn lead":            nguon,
        "Yêu cầu khách hàng":   lead.get("COMMENTS", "") or "",
    }

    if phone:
        fields["Số điện thoại"] = phone
    if email:
        fields["Email"] = email

    date_create = lead.get("DATE_CREATE", "")
    if date_create:
        # Bitrix24 trả về "2024-05-14T15:30:00+07:00" — Airtable hiểu ISO 8601
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


def notify_new_lead(lead, at_record_id):
    name_parts = [lead.get("NAME", ""), lead.get("LAST_NAME", "")]
    name = " ".join(p for p in name_parts if p).strip() or lead.get("TITLE", "Lead")

    phone_raw = lead.get("PHONE", []) or []
    phone = phone_raw[0]["VALUE"] if phone_raw else "—"

    email_raw = lead.get("EMAIL", []) or []
    email = email_raw[0]["VALUE"] if email_raw else "—"

    comments = (lead.get("COMMENTS", "") or "").strip()
    if len(comments) > 250:
        comments = comments[:250] + "…"

    at_link = f"https://airtable.com/{AIRTABLE_BASE}/{LEADS_TABLE}/{at_record_id}"

    msg = (
        f"🔔 <b>Lead mới từ Bitrix24!</b>\n\n"
        f"👤 <b>{name}</b>\n"
        f"📞 {phone}\n"
        f"📧 {email}\n"
    )
    if comments:
        msg += f"💬 {comments}\n"

    source_id = str(lead.get("SOURCE_ID", ""))
    nguon = SOURCE_MAP.get(source_id, "Khác")
    msg += (
        f"\n"
        f"📣 Nguồn: {nguon}\n"
        f"🗂 <a href='{at_link}'>Mở trong Airtable</a>\n"
        f"🔢 Bitrix24 ID: #{lead['ID']}"
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

    # 1. Lấy leads từ Bitrix24 (25 phút vừa qua)
    leads = get_bitrix_leads(since_minutes=25)
    print(f"  Bitrix24: {len(leads)} lead(s) trong 25 phút qua")

    if not leads:
        print("  Không có lead mới.")
        return

    # 2. Lấy danh sách ID đã sync để tránh duplicate
    synced = get_synced_ids()
    print(f"  Airtable: {len(synced)} Bitrix24 ID đã có")

    # 3. Sync từng lead mới
    new_count = 0
    for lead in leads:
        lead_id = str(lead["ID"])
        if lead_id in synced:
            print(f"  ↩  Lead #{lead_id} đã có — bỏ qua")
            continue

        fields = lead_to_fields(lead)
        at_id = create_record(fields)

        if at_id:
            new_count += 1
            notify_new_lead(lead, at_id)
            print(f"  ✅ Lead #{lead_id} — {fields['Tên / Nick name']} → {at_id}")

    print(f"\n✅ Xong: {new_count} lead mới được sync")


if __name__ == "__main__":
    main()
