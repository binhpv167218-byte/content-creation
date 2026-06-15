#!/usr/bin/env python3
"""
SMS Auto Sender — Zalo Extension Companion
Phát hiện khách mới trong Airtable → popup Mac xem trước + sửa → gửi SMS qua iPhone
"""

import os, time, subprocess, re
from typing import Optional
from dotenv import load_dotenv
import requests

load_dotenv('/Users/macos/Desktop/content-creation/.env')

AIRTABLE_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE = 'appwFMsNMzvK5nv2M'
TABLE_ID = 'tbl8hbsOvV2y2MnfN'
POLL_INTERVAL = 180  # 3 phút

# ── SMS Templates theo dự án ──────────────────────────────────────────────────
def build_sms(short_name: str, honorific: str, project: str) -> str:
    h = honorific or "bạn"
    H = h.capitalize()
    p = project.lower().strip()

    if "symphony" in p:
        proj_label = "Symphony 5"
    elif "fours" in p or "four s" in p:
        proj_label = "FourS Tower"
    elif "charmora" in p:
        proj_label = "Charmora"
    elif "vinhomes" in p:
        proj_label = "Vinhomes Hải Vân Bay"
    else:
        proj_label = project or "dự án"

    return (
        f"Dạ em chào {h} {short_name}, em là Bình Phan bên IQI Đà Nẵng ạ. "
        f"{H} có để lại thông tin quan tâm toà căn hộ {proj_label}, em xin kết bạn Zalo "
        f"để gửi tài liệu tổng quan trước ạ. "
        f"Tối nay nếu {h} có thời gian, cho em Bình xin 5 phút gọi điện trực tiếp được không ạ? "
        f"{H} bận thì nhắn lại thời gian {h} tiện nhất, em Bình liên lạc ngay ạ."
    )

def get_short_name(full_name: str) -> str:
    """Lấy tên gọi ngắn: 'Nguyễn Văn Minh' → 'Minh'"""
    parts = full_name.strip().split()
    return parts[-1] if parts else full_name

def get_honorific(gender: str) -> str:
    g = (gender or "").lower().strip()
    if g in ("nữ", "female", "nu"):
        return "chị"
    elif g in ("nam", "male"):
        return "anh"
    return ""

def format_phone(raw: str) -> str:
    """Chuẩn hóa số điện thoại: '0964 341 462' → '+84964341462'"""
    digits = re.sub(r'\D', '', raw)
    if digits.startswith('84'):
        return '+' + digits
    if digits.startswith('0'):
        return '+84' + digits[1:]
    return '+84' + digits

# ── Airtable ──────────────────────────────────────────────────────────────────
def fetch_new_leads():
    """Lấy các record chưa gửi SMS, có SĐT, ngày tiếp cận hôm nay hoặc chưa gửi bao giờ"""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{TABLE_ID}"
    headers = {"Authorization": f"Bearer {AIRTABLE_KEY}"}
    records, offset = [], None
    while True:
        params = {"pageSize": 100, "filterByFormula": "AND({Đã gửi SMS}=FALSE(), {Số điện thoại}!='')"}
        if offset:
            params["offset"] = offset
        r = requests.get(url, headers=headers, params=params)
        data = r.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records

def mark_sms_sent(record_id: str):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{TABLE_ID}/{record_id}"
    headers = {"Authorization": f"Bearer {AIRTABLE_KEY}", "Content-Type": "application/json"}
    requests.patch(url, headers=headers, json={"fields": {"Đã gửi SMS": True}})

GCAL_NAME = "binhpv167218@gmail.com"

def create_calendar_event(full_name: str, phone: str):
    from datetime import datetime, timedelta
    now = datetime.now()
    start = now.replace(hour=19, minute=0, second=0, microsecond=0)
    end   = start + timedelta(minutes=15)
    title = f"📞 Gọi khách mới — {full_name} {phone}"
    note  = "Đã gửi SMS sáng nay. Gọi 5 phút hỏi nhu cầu BĐS."
    safe_title = title.replace('"', "'")
    safe_note  = note.replace('"', "'")
    sy, smo, sd, sh, smi = start.year, start.month, start.day, start.hour, start.minute
    ey, emo, ed, eh, emi = end.year, end.month, end.day, end.hour, end.minute
    script = f'''
tell application "Calendar"
    set targetCal to calendar "{GCAL_NAME}"
    set startDate to current date
    set year of startDate to {sy}
    set month of startDate to {smo}
    set day of startDate to {sd}
    set hours of startDate to {sh}
    set minutes of startDate to {smi}
    set seconds of startDate to 0
    set endDate to current date
    set year of endDate to {ey}
    set month of endDate to {emo}
    set day of endDate to {ed}
    set hours of endDate to {eh}
    set minutes of endDate to {emi}
    set seconds of endDate to 0
    set newEvent to make new event at end of events of targetCal with properties {{summary:"{safe_title}", start date:startDate, end date:endDate, description:"{safe_note}"}}
    make new display alarm at end of display alarms of newEvent with properties {{trigger interval:-15}}
end tell
'''
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"  📅 Đã tạo lịch Google Calendar tối nay 19:00 cho {full_name}")
        else:
            print(f"  ⚠️  Không tạo được lịch: {result.stderr.strip()}")
    except Exception as e:
        print(f"  ⚠️  Không tạo được lịch: {e}")

# ── Mac Popup ─────────────────────────────────────────────────────────────────
def show_popup(full_name: str, phone: str, sms_text: str) -> Optional[str]:
    """
    Hiện dialog cho Bình xem + sửa nội dung SMS.
    Trả về nội dung cuối cùng nếu bấm Gửi, None nếu bấm Bỏ qua.
    """
    script = f"""
tell application "System Events"
    activate
end tell
tell application "System Events"
    set result to display dialog "SMS đến {full_name} ({phone}):" & return & return & "Nội dung (sửa trực tiếp nếu cần):" default answer "{sms_text}" buttons {{"Bỏ qua", "Gửi SMS"}} default button "Gửi SMS" with title "Xác nhận gửi SMS" with icon note
    if button returned of result is "Gửi SMS" then
        return text returned of result
    else
        return ""
    end if
end tell
"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=300
        )
        text = result.stdout.strip()
        return text if text else None
    except subprocess.TimeoutExpired:
        return None

# ── Gửi SMS qua Messages ──────────────────────────────────────────────────────
def send_sms(phone: str, message: str) -> bool:
    """Gửi SMS qua Messages app (cần iPhone đã bật Text Message Forwarding)"""
    safe_msg = message.replace('"', '\\"').replace('\n', '\\n')
    script = f"""
tell application "Messages"
    set targetService to first service whose service type = SMS
    set targetBuddy to buddy "{phone}" of targetService
    send "{safe_msg}" to targetBuddy
end tell
"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"  ⚠️  Lỗi AppleScript: {result.stderr.strip()}")
            return False
        return True
    except Exception as e:
        print(f"  ❌ Lỗi gửi SMS: {e}")
        return False

# ── Main Loop ─────────────────────────────────────────────────────────────────
def run():
    print("✅ SMS Auto Sender đang chạy — poll mỗi 3 phút")
    sent_this_session = set()

    while True:
        try:
            records = fetch_new_leads()
            new = [r for r in records if r["id"] not in sent_this_session]

            for record in new:
                f = record["fields"]
                full_name  = f.get("Tên", "").strip()
                raw_phone  = f.get("Số điện thoại", "").strip()
                gender     = f.get("Giới tính", "")
                project    = f.get("Dự án quan tâm", "")

                if not full_name or not raw_phone:
                    sent_this_session.add(record["id"])
                    continue

                short_name = get_short_name(full_name)
                honorific  = get_honorific(gender)
                phone_e164 = format_phone(raw_phone)
                sms_text   = build_sms(short_name, honorific, project)

                print(f"\n📱 Lead mới: {full_name} ({raw_phone}) — {project}")

                final_text = show_popup(full_name, raw_phone, sms_text)

                if final_text:
                    ok = send_sms(phone_e164, final_text)
                    if ok:
                        mark_sms_sent(record["id"])
                        create_calendar_event(full_name, raw_phone)
                        sent_this_session.add(record["id"])
                        print(f"  ✅ Đã gửi SMS đến {full_name}")
                    else:
                        print(f"  ❌ Gửi thất bại — thử lại lần sau")
                else:
                    sent_this_session.add(record["id"])
                    print(f"  ⏭️  Bỏ qua {full_name}")

        except Exception as e:
            print(f"⚠️  Lỗi: {e}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]

    if args and args[0] == "--test":
        # python3 sms_auto.py --test <phone> <name> <honorific> <project>
        phone   = args[1] if len(args) > 1 else "0905436789"
        name    = args[2] if len(args) > 2 else "Bình"
        honor   = args[3] if len(args) > 3 else "anh"
        project = args[4] if len(args) > 4 else "Symphony 5"
        sms     = build_sms(name, honor, project)
        phone_e164 = format_phone(phone)
        print(f"Test SMS → {phone} ({phone_e164})\n{sms}\n")
        final = show_popup(name, phone, sms)
        if final:
            ok = send_sms(phone_e164, final)
            print("✅ Đã gửi" if ok else "❌ Gửi thất bại")
        else:
            print("⏭️  Bỏ qua")
    else:
        run()
