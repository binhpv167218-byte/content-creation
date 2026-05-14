#!/usr/bin/env python3
"""
CRM Daily Report — Telegram
Gửi báo cáo tổng kết leads hàng ngày lúc 9:30 PM giờ Việt Nam.
Thông tin: tổng leads, theo giai đoạn, cần xử lý, follow-up hôm nay.
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
AIRTABLE_KEY  = ENV.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE = ENV.get("AIRTABLE_BASE_ID", "")
TG_TOKEN      = ENV.get("TELEGRAM_CRM_BOT_TOKEN", "")
TG_CHAT       = ENV.get("TELEGRAM_CHAT_ID", "")

LEADS_TABLE = "tblJxEmk2yy6FwfJQ"
AT_HEADERS  = {"Authorization": f"Bearer {AIRTABLE_KEY}", "Content-Type": "application/json"}
AT_URL      = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{LEADS_TABLE}"

TZ_VN = timezone(timedelta(hours=7))
DAYS_VN = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


# ─── Airtable ─────────────────────────────────────────────────────────────────

def get_all_leads():
    leads = []
    offset = None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        r = requests.get(AT_URL, headers=AT_HEADERS, params=params, timeout=15)
        if r.status_code != 200:
            print(f"  ⚠️  Airtable error: {r.text[:200]}")
            break
        data = r.json()
        leads.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return leads


# ─── Telegram ─────────────────────────────────────────────────────────────────

def telegram(text):
    if not TG_TOKEN or not TG_CHAT:
        print("⚠️  Telegram chưa cấu hình.")
        return
    r = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id": TG_CHAT, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )
    if r.status_code != 200:
        print(f"  ⚠️  Telegram error: {r.text[:200]}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not AIRTABLE_KEY or not AIRTABLE_BASE:
        print("❌ AIRTABLE_API_KEY hoặc AIRTABLE_BASE_ID chưa có trong .env")
        sys.exit(1)

    dt = datetime.now(TZ_VN)
    today = dt.strftime("%Y-%m-%d")
    thu = DAYS_VN[dt.weekday()]
    date_str = dt.strftime("%d/%m/%Y")

    print(f"📊 CRM Daily Report — {date_str}")

    leads = get_all_leads()
    total = len(leads)

    # Phân loại leads
    moi_nhan = []       # Chưa xử lý
    follow_up_today = []  # Follow-up đúng hôm nay
    new_today = []      # Nhận được hôm nay
    by_stage: dict[str, list] = {}

    for rec in leads:
        f = rec.get("fields", {})
        stage = f.get("Giai đoạn", "Không rõ")

        if stage not in by_stage:
            by_stage[stage] = []
        by_stage[stage].append(f)

        if stage == "Mới Nhận":
            moi_nhan.append(f)

        followup = f.get("Ngày follow-up tiếp theo", "")
        if followup and followup.startswith(today):
            follow_up_today.append(f)

        created = f.get("Thời gian lead đổ về", "")
        if created and created.startswith(today):
            new_today.append(f)

    # Build Telegram message
    msg = f"📊 <b>Báo cáo CRM — {thu}, {date_str}</b>\n\n"

    msg += f"👥 Tổng leads: <b>{total}</b>"
    if new_today:
        msg += f"  |  🆕 Hôm nay: <b>{len(new_today)}</b>"
    msg += "\n\n"

    # Stats theo giai đoạn
    stage_icons = {
        "Mới Nhận":                  "🔔",
        "Đã tiếp nhận thông tin":    "📋",
        "Quan Tâm":                  "🌟",
        "Không Quan Tâm":            "❄️",
        "Chốt":                      "🎉",
        "Bỏ":                        "🚫",
    }

    if by_stage:
        msg += "📈 <b>Theo giai đoạn:</b>\n"
        for stage, recs in sorted(by_stage.items(), key=lambda x: -len(x[1])):
            icon = stage_icons.get(stage, "•")
            msg += f"  {icon} {stage}: <b>{len(recs)}</b>\n"
        msg += "\n"

    # Leads chưa tiếp nhận (cần ưu tiên xử lý)
    if moi_nhan:
        msg += f"⚠️ <b>{len(moi_nhan)} lead Mới Nhận chưa xử lý:</b>\n"
        for f in moi_nhan[:6]:
            name = f.get("Tên / Nick name", "—")
            phone = f.get("Số điện thoại", "—")
            nguon = f.get("Nguồn lead", "")
            nguon_str = f" [{nguon}]" if nguon else ""
            msg += f"  • {name} — {phone}{nguon_str}\n"
        if len(moi_nhan) > 6:
            msg += f"  … và {len(moi_nhan) - 6} người nữa\n"
        msg += "\n"

    # Follow-up hôm nay
    if follow_up_today:
        msg += f"📅 <b>{len(follow_up_today)} cần follow-up hôm nay:</b>\n"
        for f in follow_up_today[:6]:
            name = f.get("Tên / Nick name", "—")
            phone = f.get("Số điện thoại", "—")
            stage = f.get("Giai đoạn", "")
            msg += f"  • {name} — {phone} ({stage})\n"
        if len(follow_up_today) > 6:
            msg += f"  … và {len(follow_up_today) - 6} người nữa\n"
        msg += "\n"

    if not moi_nhan and not follow_up_today:
        msg += "✅ Không có việc tồn đọng hôm nay.\n\n"

    at_link = f"https://airtable.com/{AIRTABLE_BASE}/{LEADS_TABLE}"
    msg += f"🗂 <a href='{at_link}'>Mở Airtable CRM</a>"

    telegram(msg)
    print(
        f"✅ Đã gửi báo cáo — {total} leads tổng | "
        f"{len(new_today)} mới hôm nay | "
        f"{len(moi_nhan)} chưa xử lý | "
        f"{len(follow_up_today)} follow-up hôm nay"
    )


if __name__ == "__main__":
    main()
