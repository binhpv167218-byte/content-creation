#!/usr/bin/env python3
"""
Nhắc cập nhật intelligence files mỗi 2 tuần.
Gửi Gmail + Telegram. Chạy qua GitHub Actions (trigger bởi cron-job.org).
"""

import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests

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
    env.update({k: v for k, v in os.environ.items() if v and k.isupper()})
    return env


def send_gmail(env: dict):
    sender    = env.get("GMAIL_SENDER", "")
    password  = env.get("GMAIL_APP_PASSWORD", "")
    recipient = env.get("GMAIL_RECIPIENT", "")
    if not all([sender, password, recipient]):
        print("⚠️  Thiếu Gmail config")
        return

    now       = datetime.utcnow() + timedelta(hours=7)
    date_str  = now.strftime("%d/%m/%Y")
    next_date = (now + timedelta(days=14)).strftime("%d/%m/%Y")

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:'Helvetica Neue',Arial,sans-serif;">
  <div style="max-width:520px;margin:24px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

    <div style="background:#1a1a2e;padding:24px 28px;">
      <div style="font-size:13px;color:#aaa;margin-bottom:6px;">Nhắc nhở định kỳ · {date_str}</div>
      <div style="font-size:20px;font-weight:700;color:#fff;">🧠 Cập nhật Intelligence Files</div>
    </div>

    <div style="padding:24px 28px;">
      <p style="color:#333;font-size:15px;margin-top:0;">
        Đã <strong>2 tuần</strong> kể từ lần cập nhật trước.<br>
        Viral patterns và audience pain points có thể đã lỗi thời.
      </p>

      <div style="background:#f0f7f0;border-left:4px solid #4caf50;padding:14px 16px;border-radius:4px;margin:16px 0;">
        <div style="font-size:13px;color:#555;margin-bottom:8px;">Việc cần làm:</div>
        <div style="font-size:15px;font-weight:700;color:#1a1a1a;">
          Mở Claude Code →
          gõ <code style="background:#e8f4e8;padding:3px 8px;border-radius:4px;font-size:14px;">/update-intelligence</code>
        </div>
      </div>

      <div style="font-size:13px;color:#888;margin-top:16px;">
        📦 Files sẽ được cập nhật:<br>
        &nbsp;&nbsp;· <code>context/intelligence/viral-patterns.md</code><br>
        &nbsp;&nbsp;· <code>context/intelligence/audience-painpoints.md</code>
      </div>
    </div>

    <div style="background:#f8f8f8;padding:14px 28px;border-top:1px solid #eee;">
      <div style="font-size:12px;color:#aaa;">
        Ngân sách Apify mỗi lần: ~$1.65 · Nhắc tiếp theo: {next_date}
      </div>
    </div>

  </div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🧠 Nhắc cập nhật Intelligence Files — {date_str}"
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_bytes())
    print(f"✅ Gmail gửi tới {recipient}")


def send_telegram(env: dict):
    token   = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("⚠️  Thiếu Telegram config")
        return

    now      = datetime.utcnow() + timedelta(hours=7)
    date_str = now.strftime("%d/%m/%Y")
    next_str = (now + timedelta(days=14)).strftime("%d/%m/%Y")

    text = (
        "🧠 *Nhắc cập nhật Intelligence Files*\n\n"
        "Đã 2 tuần rồi — viral patterns & pain points có thể lỗi thời.\n\n"
        "*Việc cần làm:*\n"
        "1\\. Mở Claude Code\n"
        "2\\. Gõ `/update-intelligence`\n\n"
        f"_Hôm nay: {date_str} · Nhắc tiếp: {next_str}_"
    )

    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "MarkdownV2"},
    )
    print(f"✅ Telegram gửi tới chat {chat_id}")


def main():
    print("📢 Gửi nhắc cập nhật intelligence...")
    env = load_env()
    send_gmail(env)
    send_telegram(env)
    print("Done.")


if __name__ == "__main__":
    main()
