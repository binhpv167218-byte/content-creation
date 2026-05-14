#!/usr/bin/env python3
"""
CRM Daily Report — Gmail
Gửi báo cáo tổng kết leads hàng ngày lúc 9:30 PM qua email.
Thông tin: tổng leads, theo giai đoạn, cần xử lý, follow-up hôm nay.
"""

import sys
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
AIRTABLE_KEY   = ENV.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE  = ENV.get("AIRTABLE_BASE_ID", "")
GMAIL_SENDER   = ENV.get("GMAIL_SENDER", "")
GMAIL_PASSWORD = ENV.get("GMAIL_APP_PASSWORD", "")
GMAIL_TO       = ENV.get("GMAIL_RECIPIENT", "")

LEADS_TABLE = "tblJxEmk2yy6FwfJQ"
AT_HEADERS  = {"Authorization": f"Bearer {AIRTABLE_KEY}", "Content-Type": "application/json"}
AT_URL      = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{LEADS_TABLE}"

TZ_VN   = timezone(timedelta(hours=7))
DAYS_VN = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

STAGE_COLORS = {
    "Tiếp nhận & Phân phối": "#0ea5e9",
    "Liên lạc Lại Sau":      "#f97316",
    "Máy Bận / Chưa Nghe":   "#f97316",
    "Đã Nhận Thông Tin":     "#eab308",
    "Quan Tâm":              "#22c55e",
    "Tham Quan Dự Án":       "#a855f7",
    "Tham Gia Sự Kiện":      "#a855f7",
    "Cần PIC Xác Nhận":      "#ec4899",
    "Đã Booking":            "#16a34a",
    "Giao Dịch Thành Công":  "#15803d",
    "Không Quan Tâm":        "#9ca3af",
    "Chê Giá / Tài Chính Yếu": "#ef4444",
    "Rác":                   "#dc2626",
}


# ─── Airtable ─────────────────────────────────────────────────────────────────

def get_all_leads():
    leads, offset = [], None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        r = requests.get(AT_URL, headers=AT_HEADERS, params=params, timeout=15)
        if r.status_code != 200:
            break
        data = r.json()
        leads.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return leads


# ─── Gmail ────────────────────────────────────────────────────────────────────

def send_gmail(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_SENDER
    msg["To"]      = GMAIL_TO
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_SENDER, GMAIL_PASSWORD)
        s.sendmail(GMAIL_SENDER, GMAIL_TO, msg.as_string())


def build_html(dt, today, thu, date_str, leads):
    total = len(leads)

    moi_nhan, follow_up_today, new_today = [], [], []
    by_stage: dict[str, list] = {}

    for rec in leads:
        f = rec.get("fields", {})
        stage = f.get("Giai đoạn", "Không rõ")
        by_stage.setdefault(stage, []).append(f)

        if stage in ("Mới Nhận", "Tiếp nhận & Phân phối"):
            moi_nhan.append(f)

        followup = f.get("Ngày follow-up tiếp theo", "")
        if followup and followup.startswith(today):
            follow_up_today.append(f)

        created = f.get("Thời gian lead đổ về", "")
        if created and created.startswith(today):
            new_today.append(f)

    at_link = f"https://airtable.com/{AIRTABLE_BASE}/{LEADS_TABLE}"

    # ── Stage rows ──────────────────────────────────────────────────────────
    stage_rows = ""
    for stage, recs in sorted(by_stage.items(), key=lambda x: -len(x[1])):
        color = STAGE_COLORS.get(stage, "#6b7280")
        pct   = round(len(recs) / total * 100) if total else 0
        stage_rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                         background:{color};margin-right:8px;"></span>{stage}
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;text-align:center;
                     font-weight:600;">{len(recs)}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;">
            <div style="background:#e5e7eb;border-radius:4px;height:8px;width:120px;">
              <div style="background:{color};border-radius:4px;height:8px;width:{pct}%;"></div>
            </div>
          </td>
        </tr>"""

    # ── Mới nhận rows ───────────────────────────────────────────────────────
    moi_rows = ""
    for f in moi_nhan[:10]:
        name  = f.get("Tên / Nick name", "—")
        phone = f.get("Số điện thoại", "—")
        nguon = f.get("Nguồn lead", "—")
        moi_rows += f"""
        <tr>
          <td style="padding:7px 12px;border-bottom:1px solid #f3f4f6;">{name}</td>
          <td style="padding:7px 12px;border-bottom:1px solid #f3f4f6;">{phone}</td>
          <td style="padding:7px 12px;border-bottom:1px solid #f3f4f6;color:#6b7280;">{nguon}</td>
        </tr>"""

    # ── Follow-up rows ──────────────────────────────────────────────────────
    fu_rows = ""
    for f in follow_up_today[:10]:
        name  = f.get("Tên / Nick name", "—")
        phone = f.get("Số điện thoại", "—")
        stage = f.get("Giai đoạn", "—")
        color = STAGE_COLORS.get(stage, "#6b7280")
        fu_rows += f"""
        <tr>
          <td style="padding:7px 12px;border-bottom:1px solid #f3f4f6;">{name}</td>
          <td style="padding:7px 12px;border-bottom:1px solid #f3f4f6;">{phone}</td>
          <td style="padding:7px 12px;border-bottom:1px solid #f3f4f6;">
            <span style="background:{color}22;color:{color};padding:2px 8px;
                         border-radius:12px;font-size:12px;">{stage}</span>
          </td>
        </tr>"""

    moi_section = ""
    if moi_nhan:
        moi_section = f"""
      <h2 style="font-size:16px;color:#dc2626;margin:28px 0 10px;">
        ⚠️ {len(moi_nhan)} lead chưa xử lý
      </h2>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse;font-size:14px;">
        <thead>
          <tr style="background:#fef2f2;">
            <th style="padding:8px 12px;text-align:left;color:#6b7280;font-weight:500;">Tên</th>
            <th style="padding:8px 12px;text-align:left;color:#6b7280;font-weight:500;">SĐT</th>
            <th style="padding:8px 12px;text-align:left;color:#6b7280;font-weight:500;">Nguồn</th>
          </tr>
        </thead>
        <tbody>{moi_rows}</tbody>
      </table>"""

    fu_section = ""
    if follow_up_today:
        fu_section = f"""
      <h2 style="font-size:16px;color:#0ea5e9;margin:28px 0 10px;">
        📅 {len(follow_up_today)} cần follow-up hôm nay
      </h2>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse;font-size:14px;">
        <thead>
          <tr style="background:#f0f9ff;">
            <th style="padding:8px 12px;text-align:left;color:#6b7280;font-weight:500;">Tên</th>
            <th style="padding:8px 12px;text-align:left;color:#6b7280;font-weight:500;">SĐT</th>
            <th style="padding:8px 12px;text-align:left;color:#6b7280;font-weight:500;">Giai đoạn</th>
          </tr>
        </thead>
        <tbody>{fu_rows}</tbody>
      </table>"""

    all_clear = ""
    if not moi_nhan and not follow_up_today:
        all_clear = """
      <p style="color:#16a34a;font-weight:600;margin:20px 0;">
        ✅ Không có việc tồn đọng — ngày hôm nay hoàn thành tốt!
      </p>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
             background:#f9fafb;margin:0;padding:20px;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;
              box-shadow:0 1px 3px rgba(0,0,0,.1);overflow:hidden;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1e40af,#0ea5e9);padding:28px 32px;">
      <div style="color:#bfdbfe;font-size:13px;margin-bottom:4px;">Báo cáo CRM</div>
      <div style="color:#fff;font-size:22px;font-weight:700;">{thu}, {date_str}</div>
    </div>

    <!-- Stats -->
    <div style="display:flex;gap:0;border-bottom:1px solid #f3f4f6;">
      <div style="flex:1;padding:20px 24px;border-right:1px solid #f3f4f6;text-align:center;">
        <div style="font-size:32px;font-weight:700;color:#1e40af;">{total}</div>
        <div style="font-size:12px;color:#9ca3af;margin-top:4px;">Tổng leads</div>
      </div>
      <div style="flex:1;padding:20px 24px;border-right:1px solid #f3f4f6;text-align:center;">
        <div style="font-size:32px;font-weight:700;color:#16a34a;">{len(new_today)}</div>
        <div style="font-size:12px;color:#9ca3af;margin-top:4px;">Hôm nay</div>
      </div>
      <div style="flex:1;padding:20px 24px;border-right:1px solid #f3f4f6;text-align:center;">
        <div style="font-size:32px;font-weight:700;color:#dc2626;">{len(moi_nhan)}</div>
        <div style="font-size:12px;color:#9ca3af;margin-top:4px;">Chưa xử lý</div>
      </div>
      <div style="flex:1;padding:20px 24px;text-align:center;">
        <div style="font-size:32px;font-weight:700;color:#0ea5e9;">{len(follow_up_today)}</div>
        <div style="font-size:12px;color:#9ca3af;margin-top:4px;">Follow-up</div>
      </div>
    </div>

    <!-- Body -->
    <div style="padding:24px 32px;">

      <h2 style="font-size:16px;color:#374151;margin:0 0 12px;">📈 Theo giai đoạn</h2>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse;font-size:14px;">
        <tbody>{stage_rows}</tbody>
      </table>

      {moi_section}
      {fu_section}
      {all_clear}

      <!-- CTA -->
      <div style="text-align:center;margin-top:28px;">
        <a href="{at_link}"
           style="display:inline-block;background:#1e40af;color:#fff;padding:12px 28px;
                  border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;">
          Mở Airtable CRM
        </a>
      </div>
    </div>

    <div style="padding:16px 32px;background:#f9fafb;text-align:center;
                color:#9ca3af;font-size:12px;">
      Bình Phan BĐS · Hệ thống CRM tự động
    </div>
  </div>
</body></html>"""


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not AIRTABLE_KEY or not AIRTABLE_BASE:
        print("❌ AIRTABLE_API_KEY hoặc AIRTABLE_BASE_ID chưa có")
        sys.exit(1)
    if not GMAIL_SENDER or not GMAIL_PASSWORD:
        print("❌ GMAIL_SENDER hoặc GMAIL_APP_PASSWORD chưa có")
        sys.exit(1)

    dt       = datetime.now(TZ_VN)
    today    = dt.strftime("%Y-%m-%d")
    thu      = DAYS_VN[dt.weekday()]
    date_str = dt.strftime("%d/%m/%Y")

    print(f"📊 CRM Daily Report — {date_str}")

    leads = get_all_leads()
    total = len(leads)

    new_today      = [r for r in leads if (r.get("fields", {}).get("Thời gian lead đổ về", "") or "").startswith(today)]
    moi_nhan       = [r for r in leads if r.get("fields", {}).get("Giai đoạn", "") in ("Mới Nhận", "Tiếp nhận & Phân phối")]
    follow_up_today = [r for r in leads if (r.get("fields", {}).get("Ngày follow-up tiếp theo", "") or "").startswith(today)]

    subject = f"📊 Báo cáo CRM — {thu}, {date_str} ({total} leads)"
    html    = build_html(dt, today, thu, date_str, leads)

    send_gmail(subject, html)
    print(
        f"✅ Gmail sent — {total} leads | "
        f"{len(new_today)} hôm nay | "
        f"{len(moi_nhan)} chưa xử lý | "
        f"{len(follow_up_today)} follow-up"
    )


if __name__ == "__main__":
    main()
