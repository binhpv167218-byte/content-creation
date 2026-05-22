#!/usr/bin/env python3
"""
Gửi Telegram reminder mỗi sáng: danh sách khách cần follow-up hôm nay và ngày mai.
Field "Lần" xác định lần liên hệ thứ mấy (1-4).

Chạy tự động qua GitHub Actions lúc 8:30 sáng (01:30 UTC).
"""

import os
import requests
from datetime import date, timedelta
from pathlib import Path

WORKSPACE  = Path(__file__).parent.parent
CSKH_TABLE = "tbl8hbsOvV2y2MnfN"  # 🤝 Khách Hàng

# Cadence: sau mỗi lần, cách bao nhiêu ngày đến lần tiếp theo
CADENCE = {1: 2, 2: 2, 3: 3}  # lần 1 → +2 ngày, lần 2 → +2, lần 3 → +3


def load_env():
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


def fetch_followups(at_key, at_base, target_date: date) -> list:
    headers = {"Authorization": f"Bearer {at_key}"}
    date_str = target_date.isoformat()
    params = {
        "filterByFormula": f"IS_SAME({{Ngày follow-up}},'{date_str}','day')",
        "fields[]": ["Tên", "Dự án quan tâm", "Hành động tiếp theo", "Số lần liên hệ"],
        "pageSize": 100,
    }
    r = requests.get(
        f"https://api.airtable.com/v0/{at_base}/{CSKH_TABLE}",
        headers=headers, params=params,
    )
    r.raise_for_status()
    return r.json().get("records", [])


def send_telegram(bot_token, chat_id, message):
    r = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
        timeout=15,
    )
    r.raise_for_status()


def format_record(rec, prefix=""):
    f      = rec.get("fields", {})
    name   = f.get("Tên", "Không rõ")
    project = f.get("Dự án quan tâm", "")
    action  = f.get("Hành động tiếp theo", "").strip()
    lan     = f.get("Số lần liên hệ")

    lan_tag = f" [Lần {int(lan)}/4]" if lan else ""
    line = f"{prefix}<b>{name}</b>{lan_tag}"
    if project:
        line += f" — {project}"
    if action:
        line += f"\n    {action}"

    # Gợi ý lần tiếp theo
    if lan and int(lan) < 4:
        days_next = CADENCE.get(int(lan), 3)
        line += f"\n    <i>Lần {int(lan)+1} dự kiến sau {days_next} ngày nếu không hồi âm</i>"
    elif lan and int(lan) == 4:
        line += f"\n    <i>Lần cuối — nếu không hồi âm chuyển sang Chờ sự kiện</i>"

    return line


def main():
    env       = load_env()
    at_key    = env.get("AIRTABLE_API_KEY", "")
    at_base   = env.get("AIRTABLE_BASE_ID", "")
    bot_token = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id   = env.get("TELEGRAM_CHAT_ID", "")

    if not all([at_key, at_base, bot_token, chat_id]):
        print("Thiếu biến môi trường cần thiết")
        return

    today    = date.today()
    tomorrow = today + timedelta(days=1)

    today_recs    = fetch_followups(at_key, at_base, today)
    tomorrow_recs = fetch_followups(at_key, at_base, tomorrow)

    if not today_recs and not tomorrow_recs:
        print("Không có follow-up nào hôm nay và ngày mai.")
        return

    lines = ["📋 <b>Nhắc chăm sóc khách hàng</b>"]

    if today_recs:
        lines.append(f"\n🔴 <b>Hôm nay ({today.strftime('%d/%m')}) — {len(today_recs)} khách:</b>")
        for i, rec in enumerate(today_recs, 1):
            lines.append(format_record(rec, prefix=f"{i}. "))

    if tomorrow_recs:
        lines.append(f"\n🟡 <b>Ngày mai ({tomorrow.strftime('%d/%m')}) — {len(tomorrow_recs)} khách:</b>")
        for i, rec in enumerate(tomorrow_recs, 1):
            lines.append(format_record(rec, prefix=f"{i}. "))

    message = "\n".join(lines)
    send_telegram(bot_token, chat_id, message)
    print(f"Đã gửi: {len(today_recs)} hôm nay, {len(tomorrow_recs)} ngày mai.")


if __name__ == "__main__":
    main()
