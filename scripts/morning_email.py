#!/usr/bin/env python3
"""
Gửi lịch đăng bài hôm nay qua Gmail lúc 6:00 sáng.
Chạy tự động qua GitHub Actions.

Usage:
    python3 scripts/morning_email.py
    python3 scripts/morning_email.py --date 2026-05-17
"""

import argparse
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests

WORKSPACE = Path(__file__).parent.parent

FORMAT_ICON = {
    "Ảnh cá nhân":   "🖼",
    "Carousel":       "📊",
    "AI Infographic": "📈",
}

PLATFORM_LABEL = {
    "Facebook BMN": "FB Bình Mê Nhà",
    "Facebook IQI": "FB IQI",
    "Facebook":     "Facebook",
    "TikTok":       "TikTok",
    "Instagram":    "Instagram",
    "Threads":      "Threads",
}

WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


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


def get_schedule(env: dict, target_date: str) -> list:
    r = requests.get(
        f"https://api.airtable.com/v0/{env['AIRTABLE_BASE_ID']}/tbll5ikhBQPeak8xR",
        headers={"Authorization": f"Bearer {env['AIRTABLE_API_KEY']}"},
        params={
            "fields[]": ["Số bài", "Tiêu đề", "Format", "Platform",
                         "Đăng lúc", "Hook", "Ngày đăng", "Status"],
            "sort[0][field]": "Đăng lúc",
            "sort[0][direction]": "asc",
        },
    )
    return [
        rec for rec in r.json().get("records", [])
        if rec["fields"].get("Ngày đăng") == target_date
        and rec["fields"].get("Status") == "Scheduled"
    ]


def get_totals(env: dict) -> dict:
    r = requests.get(
        f"https://api.airtable.com/v0/{env['AIRTABLE_BASE_ID']}/tbll5ikhBQPeak8xR",
        headers={"Authorization": f"Bearer {env['AIRTABLE_API_KEY']}"},
        params={"fields[]": ["Status"]},
    )
    records = r.json().get("records", [])
    return {
        "scheduled": sum(1 for rec in records if rec["fields"].get("Status") == "Scheduled"),
        "published": sum(1 for rec in records if rec["fields"].get("Status") == "Published"),
    }


def format_time(dang_luc: str) -> str:
    try:
        return dang_luc.split(" ")[1] if " " in dang_luc else dang_luc
    except Exception:
        return dang_luc


def build_html(target_date: str, records: list, totals: dict) -> str:
    try:
        d = datetime.strptime(target_date, "%Y-%m-%d")
        day_name = WEEKDAYS[d.weekday()]
        date_fmt = f"{day_name}, {d.strftime('%d/%m/%Y')}"
    except Exception:
        date_fmt = target_date

    rows = ""
    if not records:
        rows = """
        <tr>
          <td colspan="4" style="padding:20px;text-align:center;color:#888;">
            Không có bài nào được lên lịch hôm nay.
          </td>
        </tr>"""
    else:
        for rec in records:
            f = rec["fields"]
            num       = f.get("Số bài", "?")
            title     = f.get("Tiêu đề", "")
            fmt       = f.get("Format", "")
            platforms = f.get("Platform", [])
            dang_luc  = f.get("Đăng lúc", "")
            hook      = f.get("Hook", "")

            gio = format_time(dang_luc)
            icon = FORMAT_ICON.get(fmt, "📝")
            hook_text = (hook.split("\n")[0][:70] if hook else title[:70]) + ("…" if len(hook.split("\n")[0]) > 70 else "")
            platform_badges = "".join(
                f'<span style="display:inline-block;margin:2px 3px 2px 0;padding:2px 8px;'
                f'background:#e8f4e8;border-radius:10px;font-size:12px;color:#2d6a2d;">'
                f'{PLATFORM_LABEL.get(p, p)}</span>'
                for p in platforms
            )

            rows += f"""
        <tr style="border-bottom:1px solid #f0f0f0;">
          <td style="padding:12px 8px;font-weight:700;font-size:15px;color:#1a1a1a;white-space:nowrap;">
            {gio}
          </td>
          <td style="padding:12px 8px;font-size:18px;">{icon}</td>
          <td style="padding:12px 8px;">
            <div style="font-size:11px;color:#888;margin-bottom:3px;">Bài {num:02d} · {fmt}</div>
            <div style="font-size:14px;font-weight:600;color:#1a1a1a;margin-bottom:5px;">{hook_text}</div>
            <div>{platform_badges}</div>
          </td>
        </tr>"""

    total_today = len(records)
    return f"""<!DOCTYPE html>
<html lang="vi">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:'Helvetica Neue',Arial,sans-serif;">
  <div style="max-width:600px;margin:20px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

    <!-- Header -->
    <div style="background:#1a1a2e;padding:24px 28px;">
      <div style="font-size:13px;color:#aaa;margin-bottom:6px;">Kế hoạch đăng bài</div>
      <div style="font-size:22px;font-weight:700;color:#fff;">{date_fmt}</div>
      <div style="margin-top:10px;">
        <span style="background:#c8e64a;color:#1a1a1a;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:700;">
          {total_today} bài hôm nay
        </span>
      </div>
    </div>

    <!-- Schedule table -->
    <div style="padding:0 20px 20px;">
      <table style="width:100%;border-collapse:collapse;margin-top:8px;">
        {rows}
      </table>
    </div>

    <!-- Footer -->
    <div style="background:#f8f8f8;padding:16px 28px;border-top:1px solid #eee;">
      <div style="font-size:13px;color:#555;">
        📦 Tổng kho:
        <strong>{totals['scheduled']}</strong> bài chờ đăng ·
        <strong>{totals['published']}</strong> bài đã đăng
      </div>
    </div>

  </div>
</body>
</html>"""


def send_email(env: dict, subject: str, html: str):
    sender    = env.get("GMAIL_SENDER", "")
    password  = env.get("GMAIL_APP_PASSWORD", "")
    recipient = env.get("GMAIL_RECIPIENT", "")

    if not sender or not password or not recipient:
        print("⚠️  Thiếu GMAIL_SENDER / GMAIL_APP_PASSWORD / GMAIL_RECIPIENT trong .env")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_bytes())
    print(f"✅ Email gửi tới {recipient}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=(datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d"))
    args = parser.parse_args()

    env = load_env()
    target = args.date

    print(f"📅 Lấy lịch ngày {target}...")
    records = get_schedule(env, target)
    totals  = get_totals(env)
    print(f"   → {len(records)} bài hôm nay | tổng kho: {totals['scheduled']} chờ · {totals['published']} đã đăng")

    try:
        d = datetime.strptime(target, "%Y-%m-%d")
        day_name = WEEKDAYS[d.weekday()]
        subject = f"📅 Kế hoạch đăng bài — {day_name}, {d.strftime('%d/%m/%Y')} ({len(records)} bài)"
    except Exception:
        subject = f"📅 Kế hoạch đăng bài — {target}"

    html = build_html(target, records, totals)
    send_email(env, subject, html)


if __name__ == "__main__":
    main()
