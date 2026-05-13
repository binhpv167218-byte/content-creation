#!/usr/bin/env python3
"""
Gửi kế hoạch đăng bài hôm nay lên Telegram.
Chạy tự động mỗi sáng qua cron job.

Usage:
    python3 scripts/morning_briefing.py
    python3 scripts/morning_briefing.py --date 2026-05-17   # xem ngày khác
"""

import argparse
import requests
from datetime import date, datetime
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent

FORMAT_ICON = {
    "Ảnh cá nhân":   "🖼",
    "Carousel":       "📊",
    "AI Infographic": "📈",
}

PLATFORM_SHORT = {
    "Facebook":  "FB",
    "TikTok":    "TT",
    "Instagram": "IG",
    "Threads":   "Th",
}


def load_env():
    import os
    env = {}
    # Đọc từ .env nếu chạy local
    env_file = WORKSPACE / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    # Override bằng environment variables (GitHub Actions)
    for key in ["AIRTABLE_API_KEY", "AIRTABLE_BASE_ID", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]:
        if os.environ.get(key):
            env[key] = os.environ[key]
    return env


def get_schedule(target_date: str) -> list:
    env = load_env()
    at_key  = env["AIRTABLE_API_KEY"]
    at_base = env["AIRTABLE_BASE_ID"]

    # Lấy tất cả rồi lọc phía client để tránh lỗi encoding tiếng Việt trong formula
    r = requests.get(
        f"https://api.airtable.com/v0/{at_base}/tbll5ikhBQPeak8xR",
        headers={"Authorization": f"Bearer {at_key}"},
        params={
            "fields[]": ["Số bài", "Tiêu đề", "Format", "Platform", "Đăng lúc", "Hook", "Ngày đăng", "Status"],
            "sort[0][field]": "Đăng lúc",
            "sort[0][direction]": "asc",
        },
    )
    all_records = r.json().get("records", [])
    return [
        rec for rec in all_records
        if rec["fields"].get("Ngày đăng") == target_date
        and rec["fields"].get("Status") == "Scheduled"
    ]


def get_week_summary() -> dict:
    """Đếm số bài Scheduled và Published trong tuần."""
    env = load_env()
    at_key  = env["AIRTABLE_API_KEY"]
    at_base = env["AIRTABLE_BASE_ID"]

    r = requests.get(
        f"https://api.airtable.com/v0/{at_base}/tbll5ikhBQPeak8xR",
        headers={"Authorization": f"Bearer {at_key}"},
        params={"fields[]": ["Status"]},
    )
    records = r.json().get("records", [])
    scheduled = sum(1 for rec in records if rec["fields"].get("Status") == "Scheduled")
    published  = sum(1 for rec in records if rec["fields"].get("Status") == "Published")
    return {"scheduled": scheduled, "published": published}


def build_message(target_date: str, records: list, summary: dict) -> str:
    # Header
    try:
        d = datetime.strptime(target_date, "%Y-%m-%d")
        weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        day_name = weekdays[d.weekday()]
        date_fmt = f"{day_name}, {d.strftime('%d/%m/%Y')}"
    except Exception:
        date_fmt = target_date

    lines = [
        f"📅 *Kế hoạch đăng bài — {date_fmt}*",
        "",
    ]

    if not records:
        lines.append("_Không có bài nào được lên lịch hôm nay._")
    else:
        for rec in records:
            f = rec["fields"]
            num      = f.get("Số bài", "?")
            title    = f.get("Tiêu đề", "")
            fmt      = f.get("Format", "")
            platforms = f.get("Platform", [])
            dang_luc = f.get("Đăng lúc", "")
            hook     = f.get("Hook", "")

            # Lấy giờ từ "17/05/2026 19:00"
            try:
                gio = dang_luc.split(" ")[1] if " " in dang_luc else dang_luc
            except Exception:
                gio = dang_luc

            fmt_icon = FORMAT_ICON.get(fmt, "📝")
            platform_str = " · ".join(PLATFORM_SHORT.get(p, p) for p in platforms)
            hook_short = hook.split("\n")[0][:50] if hook else title[:50]

            lines.append(f"*{gio}* {fmt_icon} Bài {num:02d}")
            lines.append(f"  _{hook_short}_")
            lines.append(f"  [{fmt}] → {platform_str}")
            lines.append("")

    # Footer summary
    lines += [
        "─────────────────",
        f"📦 Tổng kho: *{summary['scheduled']}* chờ đăng · *{summary['published']}* đã đăng",
    ]

    return "\n".join(lines)


def send_telegram(message: str):
    env = load_env()
    token   = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("⚠️  Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong .env")
        return
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
    )
    if r.json().get("ok"):
        print("✅ Đã gửi Telegram")
    else:
        print(f"❌ Lỗi Telegram: {r.json()}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD")
    args = parser.parse_args()

    print(f"📅 Lấy lịch ngày {args.date}...")
    records = get_schedule(args.date)
    summary = get_week_summary()
    print(f"   → {len(records)} bài hôm nay | {summary['scheduled']} bài đang chờ")

    message = build_message(args.date, records, summary)
    print("\n--- Preview ---")
    print(message)
    print("---------------\n")

    send_telegram(message)


if __name__ == "__main__":
    main()
