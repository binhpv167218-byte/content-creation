#!/usr/bin/env python3
"""
Gửi tổng kết bài đăng hôm nay qua Gmail lúc 9:30 tối.
Bao gồm link bài viết từng kênh.

Usage:
    python3 scripts/evening_summary.py
    python3 scripts/evening_summary.py --date 2026-05-17
"""

import argparse
import os
import re
import smtplib
from datetime import date, datetime
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


def get_published_today(env: dict, target_date: str) -> list:
    r = requests.get(
        f"https://api.airtable.com/v0/{env['AIRTABLE_BASE_ID']}/tbll5ikhBQPeak8xR",
        headers={"Authorization": f"Bearer {env['AIRTABLE_API_KEY']}"},
        params={
            "fields[]": ["Số bài", "Tiêu đề", "Slug", "Format", "Platform",
                         "Đăng lúc", "Ngày đăng", "Status",
                         "Facebook ID", "Instagram ID", "TikTok ID", "Threads ID", "Ghi chú"],
            "sort[0][field]": "Đăng lúc",
            "sort[0][direction]": "asc",
        },
    )
    # Airtable lưu Ngày đăng dạng YYYY-MM-DD, Đăng lúc dạng DD/MM/YYYY HH:MM
    # Lọc bài Published trong ngày target
    results = []
    for rec in r.json().get("records", []):
        f = rec["fields"]
        if f.get("Status") != "Published":
            continue
        # Kiểm tra Ngày đăng
        if f.get("Ngày đăng") == target_date:
            results.append(rec)
            continue
        # Fallback: parse Đăng lúc nếu Ngày đăng không khớp
        dang_luc = f.get("Đăng lúc", "")
        try:
            dt = datetime.strptime(dang_luc, "%d/%m/%Y %H:%M")
            if dt.strftime("%Y-%m-%d") == target_date:
                results.append(rec)
        except ValueError:
            pass
    return results


def extract_links(fields: dict) -> list:
    """Trả về list (label, url) cho các kênh đã đăng thành công."""
    links = []

    fb_id = fields.get("Facebook ID", "")
    if fb_id:
        links.append(("Facebook", f"https://www.facebook.com/{fb_id}"))

    # Parse Ghi chú để lấy thêm link Facebook BMN và kết quả các kênh khác
    ghi_chu = fields.get("Ghi chú", "")
    if ghi_chu:
        for line in ghi_chu.splitlines():
            if "Facebook BMN:" in line and "LỖI" not in line:
                url = re.search(r"https?://\S+", line)
                if url:
                    links.append(("Facebook BMN", url.group()))
            elif "Facebook IQI:" in line and "LỖI" not in line and not fb_id:
                url = re.search(r"https?://\S+", line)
                if url:
                    links.append(("Facebook IQI", url.group()))
            elif "Instagram:" in line and "LỖI" not in line:
                links.append(("Instagram", ""))   # Buffer ID, không có link trực tiếp
            elif "TikTok:" in line and "LỖI" not in line:
                links.append(("TikTok", ""))
            elif "Threads:" in line and "LỖI" not in line:
                links.append(("Threads", ""))

    # Deduplicate: ưu tiên giữ entry có URL
    seen = {}
    for label, url in links:
        base = label.split(" ")[0]  # "Facebook BMN" → "Facebook"
        if base not in seen or url:
            seen[base] = (label, url)
    return list(seen.values())


def count_errors(ghi_chu: str) -> int:
    return sum(1 for line in ghi_chu.splitlines() if "LỖI" in line)


def build_html(target_date: str, records: list) -> str:
    try:
        d = datetime.strptime(target_date, "%Y-%m-%d")
        day_name = WEEKDAYS[d.weekday()]
        date_fmt = f"{day_name}, {d.strftime('%d/%m/%Y')}"
    except Exception:
        date_fmt = target_date

    total = len(records)

    if not records:
        body = """
        <div style="padding:30px;text-align:center;color:#888;">
          Hôm nay chưa có bài nào được đăng.
        </div>"""
    else:
        cards = ""
        for rec in records:
            f = rec["fields"]
            num       = f.get("Số bài", "?")
            title     = f.get("Tiêu đề", "")
            fmt       = f.get("Format", "")
            platforms = f.get("Platform", [])
            dang_luc  = f.get("Đăng lúc", "")
            ghi_chu   = f.get("Ghi chú", "")
            icon      = FORMAT_ICON.get(fmt, "📝")

            try:
                gio = dang_luc.split(" ")[1] if " " in dang_luc else dang_luc
            except Exception:
                gio = dang_luc

            links = extract_links(f)
            errors = count_errors(ghi_chu)

            link_html = ""
            for label, url in links:
                if url:
                    link_html += (
                        f'<a href="{url}" style="display:inline-block;margin:3px 4px 3px 0;'
                        f'padding:4px 12px;background:#1a73e8;color:#fff;border-radius:14px;'
                        f'font-size:12px;text-decoration:none;">{label} →</a>'
                    )
                else:
                    link_html += (
                        f'<span style="display:inline-block;margin:3px 4px 3px 0;'
                        f'padding:4px 12px;background:#34a853;color:#fff;border-radius:14px;'
                        f'font-size:12px;">✓ {label}</span>'
                    )

            error_badge = ""
            if errors:
                error_badge = (
                    f'<span style="margin-left:8px;padding:2px 8px;background:#fce8e6;'
                    f'color:#c5221f;border-radius:10px;font-size:11px;">{errors} lỗi</span>'
                )

            platform_str = " · ".join(platforms)

            cards += f"""
        <div style="margin:0 0 16px 0;padding:16px 20px;border:1px solid #e8e8e8;border-radius:10px;">
          <div style="display:flex;align-items:center;margin-bottom:8px;">
            <span style="font-size:20px;margin-right:10px;">{icon}</span>
            <div>
              <div style="font-size:13px;color:#888;">Bài {num:02d} · {gio} · {fmt}</div>
              <div style="font-size:15px;font-weight:700;color:#1a1a1a;">{title}</div>
            </div>
            {error_badge}
          </div>
          <div style="font-size:12px;color:#666;margin-bottom:10px;">{platform_str}</div>
          <div>{link_html if link_html else '<span style="color:#aaa;font-size:12px;">Không có link trực tiếp</span>'}</div>
        </div>"""

        body = f'<div style="padding:20px;">{cards}</div>'

    status_color = "#34a853" if total > 0 else "#888"

    return f"""<!DOCTYPE html>
<html lang="vi">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:'Helvetica Neue',Arial,sans-serif;">
  <div style="max-width:600px;margin:20px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

    <!-- Header -->
    <div style="background:#1a1a2e;padding:24px 28px;">
      <div style="font-size:13px;color:#aaa;margin-bottom:6px;">Tổng kết đăng bài</div>
      <div style="font-size:22px;font-weight:700;color:#fff;">{date_fmt}</div>
      <div style="margin-top:10px;">
        <span style="background:{status_color};color:#fff;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:700;">
          {total} bài đã đăng hôm nay
        </span>
      </div>
    </div>

    <!-- Cards -->
    {body}

    <!-- Footer -->
    <div style="background:#f8f8f8;padding:14px 28px;border-top:1px solid #eee;">
      <div style="font-size:12px;color:#999;">
        Bình Phan BĐS · Hệ thống đăng tự động
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
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    env = load_env()
    target = args.date

    print(f"📊 Lấy bài đã đăng ngày {target}...")
    records = get_published_today(env, target)
    print(f"   → {len(records)} bài đã đăng")

    try:
        d = datetime.strptime(target, "%Y-%m-%d")
        day_name = WEEKDAYS[d.weekday()]
        subject = f"📊 Tổng kết đăng bài — {day_name}, {d.strftime('%d/%m/%Y')} ({len(records)} bài)"
    except Exception:
        subject = f"📊 Tổng kết đăng bài — {target}"

    html = build_html(target, records)
    send_email(env, subject, html)


if __name__ == "__main__":
    main()
