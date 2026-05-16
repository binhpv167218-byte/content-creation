#!/usr/bin/env python3
"""
Gửi Telegram reminder mỗi sáng: danh sách khách cần follow-up hôm nay và ngày mai.

Chạy tự động qua GitHub Actions lúc 7:00 sáng (00:00 UTC).
"""

import os
import json
import requests
from datetime import date, timedelta
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
CSKH_TABLE = "tblOU5r9U7qZBpjvP"


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
        "filterByFormula": f"{{Ngày follow-up}}='{date_str}'",
        "fields[]": ["Khách hàng", "Dự án đề cập", "Hành động tiếp theo", "Ngày follow-up"],
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
    f = rec.get("fields", {})
    name    = f.get("Khách hàng", "Không rõ")
    project = f.get("Dự án đề cập", "")
    action  = f.get("Hành động tiếp theo", "").strip()
    line = f"{prefix}<b>{name}</b>"
    if project:
        line += f" ({project})"
    if action:
        line += f"\n    {action}"
    return line


def main():
    env        = load_env()
    at_key     = env.get("AIRTABLE_API_KEY", "")
    at_base    = env.get("AIRTABLE_BASE_ID", "")
    bot_token  = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id    = env.get("TELEGRAM_CHAT_ID", "")

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
