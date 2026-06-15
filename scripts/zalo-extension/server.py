#!/usr/bin/env python3
"""
Zalo Extension Local Server
Nhận chat data từ Chrome Extension → phân tích phase → update Airtable
"""

import os, json, re, subprocess
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from google import genai as google_genai
import requests
from difflib import SequenceMatcher

load_dotenv('/Users/macos/Desktop/content-creation/.env')

AIRTABLE_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE = os.getenv('AIRTABLE_BASE_ID', 'appwFMsNMzvK5nv2M')
TABLE_ID = 'tbl8hbsOvV2y2MnfN'

gemini = google_genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_FALLBACK = "gemini-2.5-flash-lite"

PHASE_DESCRIPTIONS = {
    "A": "Bắt Lead Nóng — vừa có lead, chưa xác định nhu cầu",
    "B": "Xây Dựng Tin Tưởng — đang gửi thông tin, giới thiệu dự án",
    "C": "Nuôi Dưỡng — đang follow up, gửi thêm góc nhìn đầu tư",
    "D": "Đánh Giá — đang bàn giá, chính sách, mời xem thực địa",
    "E": "Thúc Đẩy Quyết Định — đang push booking, xử lý objection",
    "F": "Dài Hạn — đã booking hoặc đang chăm sóc sau",
}

NEXT_STEP_SHORTCUTS = {
    "A": [";cha", ";nha", ";zla"],
    "B": [";bia", ";s5a", ";fta"],
    "C": [";vta", ";dta", ";fua"],
    "D": [";gia", ";tda", ";csa"],
    "E": [";50a", ";sga", ";bka", ";cka"],
    "F": [";f2a", ";cma"],
}

THINK_KEYWORDS = [
    "để suy nghĩ", "suy nghĩ thêm", "nghĩ thêm", "để tính",
    "cân nhắc thêm", "để xem", "để hỏi", "chờ tôi", "để anh nghĩ",
    "để chị nghĩ", "để mình nghĩ", "tính lại", "chưa quyết",
    "chờ em", "hỏi vợ", "hỏi chồng", "bàn với",
]

FAREWELL_KEYWORDS = [
    "tạm biệt", "bye", "good night", "ngủ ngon", "chúc ngủ ngon",
    "ok em", "ok nhé", "cảm ơn em", "cảm ơn bình", "thanks", "thank you",
    "anh hiểu rồi", "chị hiểu rồi", "mình hiểu rồi", "rõ rồi em",
    "để anh xem", "để chị xem", "anh xem thêm", "chị xem thêm",
    "ok anh/chị sẽ", "hẹn gặp", "hẹn nói chuyện",
]

# Phase-based timing config: (think_days, think_hour, no_reply_days, no_reply_hour, urgency_label)
# think = khách nói "suy nghĩ thêm"
# no_reply = tin cuối là của Bình, khách im
PHASE_TIMING = {
    "A": (1, 19, 0, 17, "tối nay"),           # Hot lead mới: nhắn lại tối cùng ngày
    "B": (1, 19, 1,  9, "sáng mai"),          # Đang xây dựng tin tưởng: 1 ngày
    "C": (2, 19, 2, 19, "19-21h ngày kia"),   # Nuôi dưỡng: 2 ngày OK
    "D": (1, 19, 1, 19, "ngày mai tối"),      # Đang đánh giá: 1 ngày
    "E": (1, 19, 1, 19, "ngày mai tối"),      # Sắp quyết định: 1 ngày, không để lâu
    "F": (4, 10, 5, 10, "đầu tuần sau"),      # Dài hạn: có thể thư thả hơn
}

def detect_timing_rules(messages, phase="C", hours_since_last=None, project=""):
    """Phase-aware timing rules. phase từ AI analysis, hours_since_last từ timestamp nếu có."""
    if not messages:
        return None

    # Rule 0: Symphony 5 mở bán chính thức 27/05/2026 — ưu tiên tuyệt đối
    if "symphony" in project.lower():
        opening_date = datetime(2026, 5, 27)
        now = datetime.now()
        days_to_opening = (opening_date.date() - now.date()).days
        if -1 <= days_to_opening <= 1:          # 26/5 → 28/5
            if days_to_opening >= 0 and now.hour < 20:
                label = "tối nay trước 20h" if days_to_opening == 0 else "ngày mai trước mở bán"
                return {
                    "should_message": True,
                    "urgency": label,
                    "reason": f"Symphony 5 mở bán chính thức 27/05 — có thể update thông tin mới cho khách nếu họ đang quan tâm",
                    "wait_days": 0 if days_to_opening == 0 else 1,
                    "follow_up_hour": 19,
                }
            elif days_to_opening < 0:           # 28/5 trở đi: vừa mở bán, update tự nhiên
                return {
                    "should_message": True,
                    "urgency": "hôm nay",
                    "reason": "Symphony 5 vừa mở bán — có thể chia sẻ cập nhật tình hình nếu khách đang quan tâm, không cần push",
                    "wait_days": 0,
                    "follow_up_hour": 10,
                }

    cfg = PHASE_TIMING.get(phase, PHASE_TIMING["C"])
    think_days, think_hour, no_reply_days, no_reply_hour, urgency_label = cfg

    # Điều chỉnh no_reply_days=0 (tối nay): nếu đã qua 17h thì dời sang sáng mai
    def resolve_wait(days, hour):
        if days == 0:
            now_h = datetime.now().hour
            if now_h >= hour:
                return 1, 9, "sáng mai"  # đã qua giờ follow-up, dời sang sáng mai
            return 0, hour, "tối nay"
        return days, hour, urgency_label

    # Rule 1: Khách nói "suy nghĩ thêm"
    customer_msgs = [m for m in messages if not m.get("is_me")]
    if customer_msgs:
        last_customer_text = customer_msgs[-1]["text"].lower()
        if any(k in last_customer_text for k in THINK_KEYWORDS):
            wd, wh, ulabel = resolve_wait(think_days, think_hour)
            phase_note = {
                "A": "Lead mới — đừng để quá lâu, follow lại nhẹ sau 1 ngày",
                "B": "Đang xây dựng quan hệ — cho 1 ngày để khách nghĩ, rồi gửi thêm góc nhìn",
                "C": "Nuôi dưỡng — 2 ngày là hợp lý, đừng dồn",
                "D": "Đang đánh giá thật sự — 1 ngày, sau đó hỏi thêm rào cản",
                "E": "Gần chốt — tối đa 1 ngày, dự án đang hot nên không để lâu",
                "F": "Khách dài hạn — cho khách thở, 3-4 ngày mới liên hệ",
            }.get(phase, "Chờ đúng thời điểm")
            return {
                "should_message": False,
                "urgency": ulabel,
                "reason": f"Khách đang suy nghĩ (Phase {phase}) — {phase_note}. Nhắn lại {ulabel}.",
                "wait_days": wd,
                "follow_up_hour": wh,
            }

    # Rule 2: Tin cuối là của Bình, khách chưa reply
    if messages[-1].get("is_me"):
        consecutive = 0
        for m in reversed(messages):
            if m.get("is_me"):
                consecutive += 1
            else:
                break

        if consecutive >= 1:
            recent_texts = " ".join(m["text"].lower() for m in messages[-6:])
            is_farewell = any(k in recent_texts for k in FAREWELL_KEYWORDS)

            if is_farewell:
                # Cuộc trò chuyện kết thúc tự nhiên: follow-up sáng hôm sau
                return {
                    "should_message": True,
                    "urgency": "sáng mai 9h",
                    "reason": "Cuộc trò chuyện kết thúc tốt — follow-up sáng mai nếu có tin mới có giá trị",
                    "wait_days": 1,
                    "follow_up_hour": 9,
                }

            if consecutive >= 2:
                # Bình nhắn nhiều lần không có reply
                # Dùng hours_since_last nếu có để đánh giá đã chờ đủ chưa
                if hours_since_last is not None and hours_since_last < no_reply_days * 24:
                    still_wait = round(no_reply_days * 24 - hours_since_last)
                    return {
                        "should_message": False,
                        "urgency": f"chờ thêm ~{still_wait}h nữa",
                        "reason": f"Khách chưa reply — đã nhắn cách đây {round(hours_since_last)}h, nên chờ đủ {no_reply_days} ngày trước khi follow. Phase {phase}.",
                        "wait_days": no_reply_days,
                        "follow_up_hour": no_reply_hour,
                    }

                wd, wh, ulabel = resolve_wait(no_reply_days, no_reply_hour)
                return {
                    "should_message": False,
                    "urgency": ulabel,
                    "reason": f"Khách chưa phản hồi (Phase {phase}) — follow-up {ulabel} với nội dung có giá trị mới, không nhắn thêm bây giờ",
                    "wait_days": wd,
                    "follow_up_hour": wh,
                }

    return None


# File lưu mapping: customer_name → reminder ID
REMINDERS_FILE = "/tmp/zalo_reminders.json"

def _load_reminders():
    try:
        with open(REMINDERS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def _save_reminders(data):
    try:
        with open(REMINDERS_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def delete_reminder_for_customer(customer_name):
    """Xóa calendar event cũ của khách trong Google Calendar."""
    data = _load_reminders()
    entry = data.get(customer_name, {})
    title = entry.get("title", f"📞 Follow-up {customer_name}")
    safe_title = title.replace('"', "'")

    script = f'''
tell application "Calendar"
    set targetCal to calendar "{GCAL_NAME}"
    set found to (events of targetCal whose summary is "{safe_title}")
    if length of found > 0 then
        repeat with ev in found
            delete ev
        end repeat
        return "deleted"
    end if
    return "not found"
end tell
'''
    deleted = False
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
        deleted = "deleted" in r.stdout
    except Exception:
        pass

    data.pop(customer_name, None)
    _save_reminders(data)
    print(f"Calendar event deleted for: {customer_name} (found={deleted})", flush=True)
    return deleted


GCAL_NAME = "binhpv167218@gmail.com"

def create_calendar_event(event_key, display_name, wait_days, hour=19, reason=""):
    """Tạo event trong Google Calendar (sync iPhone) kèm alarm 15 phút trước.
    event_key: khóa trong reminders.json (= call_name)
    display_name: tên hiển thị trong Calendar (ưu tiên tên đầy đủ từ Airtable)
    """
    target = datetime.now() + timedelta(days=wait_days)
    target = target.replace(hour=hour, minute=0, second=0, microsecond=0)
    end_target = target + timedelta(minutes=15)

    title = f"📞 Follow-up {display_name}"
    note = reason or f"Follow-up {display_name} qua Zalo"
    safe_title = title.replace('"', "'")
    safe_note = note.replace('"', "'")

    sy, smo, sd = target.year, target.month, target.day
    sh, smi = target.hour, target.minute
    esy, esmo, esd = end_target.year, end_target.month, end_target.day
    esh, esmi = end_target.hour, end_target.minute

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
    set year of endDate to {esy}
    set month of endDate to {esmo}
    set day of endDate to {esd}
    set hours of endDate to {esh}
    set minutes of endDate to {esmi}
    set seconds of endDate to 0
    set newEvent to make new event at end of events of targetCal with properties {{summary:"{safe_title}", start date:startDate, end date:endDate, description:"{safe_note}"}}
    make new display alarm at end of display alarms of newEvent with properties {{trigger interval:-15}}
    return uid of newEvent
end tell
'''
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            rid = result.stdout.strip()
            data = _load_reminders()
            data[event_key] = {"id": rid, "title": title, "created_at": datetime.now().isoformat(), "target_date": target.date().isoformat()}
            _save_reminders(data)
            print(f"Calendar event created: {title} at {target.strftime('%d/%m %H:%M')}", flush=True)
            return True
        else:
            print(f"Calendar error: {result.stderr}", flush=True)
            return False
    except Exception as e:
        print(f"Calendar error: {e}", flush=True)
        return False


def get_all_customers():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{TABLE_ID}"
    headers = {"Authorization": f"Bearer {AIRTABLE_KEY}"}
    records = []
    offset = None
    while True:
        params = {"pageSize": 100}  # Không filter fields để tránh UNKNOWN_FIELD_NAME
        if offset:
            params["offset"] = offset
        r = requests.get(url, headers=headers, params=params)
        data = r.json()
        if "error" in data:
            print(f"Airtable error: {data['error']}", flush=True)
            break
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records

# Bình đặt tên Zalo theo format "Dự án + [Loại căn] + Tên", ví dụ "Symphony 5 Studio Chị Lan"
APARTMENT_TYPES = {
    "studio", "1pn", "1pn+", "2pn", "2pn+", "3pn", "3pn+",
    "1br", "1br+", "2br", "2br+", "3br",
    "penthouse", "shophouse", "duplex", "officetel",
}

PROJECT_PREFIXES = [
    "symphony 5", "fours tower", "fours", "four s",
    "vinhomes hai van bay", "vinhomes hvb", "vinhomes",
    "charmora", "sun charmora", "charmora onsen",
    "nobu", "m landmark", "masterise",
]

# Từ xưng hô tiếng Việt hay đứng trước tên — bỏ để match chính xác hơn
HONORIFICS = ["chị", "anh", "em", "chú", "bác", "cô", "ông", "bà", "chú", "thầy", "bạn"]

# Địa danh 2 chữ hay xuất hiện sau tên khách trong Zalo của Bình
PROVINCE_SUFFIXES_2 = {
    "lào cai", "hà nội", "hải phòng", "cần thơ", "đà nẵng",
    "bình dương", "đồng nai", "long an", "nghệ an", "thanh hóa",
    "vĩnh phúc", "kiên giang", "bến tre", "tiền giang", "tây ninh",
    "an giang", "quảng nam", "khánh hòa", "lâm đồng", "gia lai",
    "kon tum", "đắk lắk", "đắk nông", "phú yên", "ninh thuận",
    "hưng yên", "quảng bình", "quảng trị", "hà tĩnh", "hà giang",
    "cao bằng", "bắc kạn", "lạng sơn", "tuyên quang", "yên bái",
    "sơn la", "điện biên", "lai châu", "phú thọ", "thái nguyên",
    "bắc giang", "quảng ninh", "hải dương", "hà nam", "nam định",
    "thái bình", "ninh bình", "quảng ngãi", "bình định", "bình phước",
    "đồng tháp", "vĩnh long", "trà vinh", "sóc trăng", "bạc liêu",
    "cà mau", "hậu giang",
}

def get_calling_name(zalo_name: str) -> tuple[str, str]:
    """Trả về (tên gọi, xưng hô gợi ý).
    Luật: bỏ project prefix → bỏ xưng hô → bỏ địa danh cuối → lấy từ cuối còn lại.
    'Symphony 5 Mỹ Thục'          → ('Thục', '')
    'Symphony 5 Chị Hằng Lào Cai' → ('Hằng', 'chị')
    'Anh Thi'                      → ('Thi', 'anh')
    'FourS Nguyễn Mỹ Thục'        → ('Thục', '')
    """
    name_part, _ = strip_project_prefix(zalo_name)  # đã bỏ project + apt type
    words = name_part.strip().split()

    # Tách xưng hô đầu
    address = ""
    if words and words[0].lower() in HONORIFICS:
        address = words[0].lower()
        words = words[1:]

    if not words:
        return name_part, address

    # Bỏ địa danh 2 chữ ở cuối ("Lào Cai", "Hà Nội"...)
    if len(words) >= 3:
        last_two = (words[-2] + " " + words[-1]).lower()
        if last_two in PROVINCE_SUFFIXES_2:
            words = words[:-2]

    # Bỏ địa danh 3 chữ: "Hồ Chí Minh"
    if len(words) >= 4:
        last_three = " ".join(w.lower() for w in words[-3:])
        if last_three == "hồ chí minh":
            words = words[:-3]

    if not words:
        return name_part, address

    # Từ cuối còn lại = tên gọi
    return words[-1], address

def strip_project_prefix(zalo_name: str) -> tuple[str, str]:
    """Tách project prefix + loại căn, trả về (phần tên còn lại, tên dự án).
    'Symphony 5 Studio Chị Lan' → ('Chị Lan', 'Symphony 5'), apt='Studio'
    """
    lower = zalo_name.lower().strip()
    detected_project = ""
    remainder = zalo_name
    for prefix in PROJECT_PREFIXES:
        if lower.startswith(prefix):
            remainder = zalo_name[len(prefix):].strip()
            detected_project = prefix.title()
            break
    # Bỏ thêm loại căn nếu từ đầu tiên còn lại là apartment type
    words = remainder.split()
    if words and words[0].lower() in APARTMENT_TYPES:
        remainder = " ".join(words[1:]).strip()
    return (remainder or zalo_name), detected_project

def detect_apt_type(zalo_name: str) -> str:
    """Trích loại căn từ tên Zalo nếu có. 'Symphony 5 1PN+ Chị Lan' → '1PN+'"""
    _, project = _raw_strip_project(zalo_name)
    after_project = zalo_name[len(project):].strip() if project else zalo_name
    words = after_project.split()
    if words and words[0].lower() in APARTMENT_TYPES:
        return words[0].upper().replace("PN", "PN").replace("BR", "BR")
    return ""

def _raw_strip_project(zalo_name: str) -> tuple[str, str]:
    """Chỉ bỏ project prefix, không bỏ apt type."""
    lower = zalo_name.lower().strip()
    for prefix in PROJECT_PREFIXES:
        if lower.startswith(prefix):
            return zalo_name[len(prefix):].strip(), prefix
    return zalo_name, ""

def strip_honorific(name: str) -> str:
    """Bỏ xưng hô đầu tên: 'Chị Hằng' → 'Hằng', 'Anh Thi' → 'Thi'"""
    words = name.strip().split()
    if words and words[0].lower() in HONORIFICS:
        return " ".join(words[1:])
    return name

def name_variants(name: str) -> list[str]:
    """Tạo các biến thể của tên để thử match:
    'Chị Hằng Lào Cai' → ['Chị Hằng Lào Cai', 'Hằng Lào Cai', 'Hằng', ...]
    """
    variants = [name]
    no_honorific = strip_honorific(name)
    if no_honorific != name:
        variants.append(no_honorific)
    # Thêm từng từ đơn lẻ (trừ từ xưng hô)
    for w in no_honorific.split():
        if w.lower() not in HONORIFICS and len(w) > 1:
            variants.append(w)
    # Bỏ 1-2 từ cuối (có thể là tỉnh/thành: "Hằng Lào Cai" → "Hằng")
    words = no_honorific.split()
    if len(words) > 2:
        variants.append(" ".join(words[:-1]))
    if len(words) > 3:
        variants.append(" ".join(words[:-2]))
    return list(dict.fromkeys(variants))  # deduplicate, giữ thứ tự

def extract_phone_suffix_from_name(zalo_name):
    """Tách 3 số cuối SĐT nếu tên Zalo kết thúc bằng 3 chữ số. VD: 'Symphony 5 Anh Minh 407' → '407'"""
    m = re.search(r'\b(\d{3})\s*$', zalo_name.strip())
    return m.group(1) if m else ""

def fuzzy_match(zalo_name, customers, phone_hint=""):
    """Tìm khách trong Airtable dựa trên tên Zalo.
    - Tự nhận diện 3 số cuối SĐT từ tên Zalo (ưu tiên tuyệt đối nếu match)
    - Nếu nhiều kết quả → trả về tất cả để Bình chọn
    """
    # Ưu tiên: 3 số cuối từ tên Zalo
    phone_suffix = extract_phone_suffix_from_name(zalo_name)
    # Fallback: phone_hint thủ công (nếu vẫn còn truyền vào)
    if not phone_suffix and phone_hint:
        phone_suffix = re.sub(r'\D', '', phone_hint)[-3:]

    # Bỏ 3 số cuối khỏi tên trước khi match
    clean_zalo_name = re.sub(r'\s*\d{3}\s*$', '', zalo_name).strip() if phone_suffix else zalo_name
    customer_name, detected_project = strip_project_prefix(clean_zalo_name)
    variants = name_variants(customer_name)
    full_clean = clean_zalo_name.lower().strip()

    matches = []
    for c in customers:
        airtable_name = c["fields"].get("Tên", "")
        if not airtable_name:
            continue
        at_clean = airtable_name.lower().strip()
        at_no_honorific = strip_honorific(airtable_name).lower().strip()
        project_field = c["fields"].get("Dự án quan tâm", "").lower()
        at_phone = re.sub(r'\D', '', c["fields"].get("Số điện thoại", ""))

        # Ưu tiên tuyệt đối: match 3 số cuối SĐT từ tên Zalo
        if phone_suffix and at_phone.endswith(phone_suffix):
            matches.append({"record": c, "score": 10.0, "name": airtable_name})
            continue

        # Lấy score cao nhất từ tất cả biến thể tên
        best_score = 0.0
        for v in variants:
            v_clean = v.lower().strip()
            s1 = SequenceMatcher(None, v_clean, at_clean).ratio()
            s2 = SequenceMatcher(None, v_clean, at_no_honorific).ratio()
            best_score = max(best_score, s1, s2)

        # Backup: match toàn bộ zalo name
        best_score = max(best_score, SequenceMatcher(None, full_clean, at_clean).ratio())

        # Bonus: word overlap
        variant_words = set(variants[-1].lower().split()) if variants else set()
        at_words = set(at_no_honorific.split())
        common = variant_words & at_words
        meaningful_common = {w for w in common if len(w) > 1 and w not in HONORIFICS}
        if meaningful_common:
            best_score += 0.3 * len(meaningful_common)

        # Bonus: cùng dự án
        if detected_project and detected_project.lower() in project_field:
            best_score += 0.15

        if best_score > 0.4:
            matches.append({"record": c, "score": best_score, "name": airtable_name})

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:5]

def analyze_phase(chat_messages, customer_name, customer_location="", honorific="", airtable_context=""):
    """Dùng Claude để phân tích phase + loại khách + kỹ thuật tâm lý"""
    chat_text = "\n".join([
        f"{'[Bình]' if m['is_me'] else '[Khách]'}: {m['text']}"
        for m in chat_messages[-30:]
    ])

    location_context = ""
    if customer_location:
        is_danang = any(k in customer_location.lower() for k in ["đà nẵng", "da nang", "dn"])
        if is_danang:
            location_context = f"\nVỊ TRÍ KHÁCH: {customer_location} — đang ở Đà Nẵng, có thể mời xem thực địa khi phù hợp."
        else:
            location_context = f"\nVỊ TRÍ KHÁCH: {customer_location} — không ở Đà Nẵng, KHÔNG đề xuất xem thực địa."

    context_section = ""
    if airtable_context:
        context_section = f"\nGHI CHÚ AIRTABLE (lịch sử tương tác trước):\n{airtable_context}\n"

    prompt = f"""Bạn là Bình Phan — sales BĐS IQI Đà Nẵng, 10 năm kinh nghiệm. Viết tiếng Việt chuẩn, không sai chính tả. Đọc toàn bộ thông tin về khách {customer_name} rồi làm 3 việc:
1. Phân loại loại khách (dựa vào chat + ghi chú Airtable)
2. Xác định phase tư vấn
3. Viết tin nhắn tiếp theo với kỹ thuật tâm lý phù hợp{context_section}

PHÂN LOẠI KHÁCH — đọc chat + ghi chú Airtable để xác định:
- ĐT = Đầu Tư: hỏi lợi suất, cho thuê, tăng giá, ROI — không quan tâm tiện ích sống
- Ở = Mua Để Ở: hỏi tiện ích, trường học, mặt bằng, phù hợp gia đình, vị trí sinh hoạt
- Quyết Nhanh = khách đã hỏi kỹ, tín hiệu sẵn sàng rõ, cần hỗ trợ bước tiếp — KHÔNG phải tạo áp lực thêm, chỉ cần thu nhỏ bước tiếp theo
- Hoài Nghi = Khách Nghi: đặt câu hỏi khó về pháp lý/rủi ro/chủ đầu tư, thái độ thăm dò

TRIẾT LÝ CỐT LÕI — quan trọng hơn mọi kỹ thuật:
Khách hàng phải cảm giác họ đang MUA, không phải đang bị BÁN. Họ cảm giác mình đang làm chủ cuộc chơi, tự quyết định theo giá trị và nhu cầu của chính họ — dù thực tế Bình đang dẫn dắt từng bước.

Cách tạo cảm giác đó:
- Dùng lại TỪ KHÓA của khách: khi khách nói "em lo pháp lý" → đáp lại bằng "pháp lý" chứ không phải "rủi ro" hay "điểm cần lưu ý". Họ nghe lại ngôn ngữ của chính mình thì cảm giác được hiểu.
- Hỏi trước, gửi sau: luôn xin phép trước khi gửi thông tin ("Em gửi anh file tỷ suất được không ạ?" thay vì gửi thẳng). Họ đồng ý = họ chủ động nhận, không phải bị nhồi.
- Để họ tự rút kết luận: đưa dữ liệu thật + im lặng. Không kết luận thay họ. "S1-S3 lấp đầy 72-80%, em gửi anh xem" — không thêm "nên anh yên tâm đầu tư được".
- Tham chiếu lại điều họ nói trước: "Anh có nói quan trọng nhất là dòng tiền — theo tiêu chí đó thì..." Họ cảm giác quyết định xuất phát từ chính họ.
- Cho họ lựa chọn, không ra lệnh: "Anh muốn em gửi thêm về tỷ suất hay về chính sách thanh toán trước ạ?" — dù cả hai đều là thông tin Bình muốn gửi.
- Không bao giờ tạo áp lực thay thế việc tạo giá trị: nếu khách chưa thấy đủ lý do thì thêm thông tin, không thêm deadline.

PHASE + CÁCH TIẾP CẬN — đúng giai đoạn, không nhảy trước:

A = Bắt Lead Nóng (khách mới, chưa biết gì về nhau)
  → MỤC TIÊU: hiểu khách đang cần gì — CHƯA giới thiệu dự án
  → CÁCH: lắng nghe + hỏi mở 1 câu thôi, lặp lại từ chính khách dùng để tạo cảm giác được hiểu
  → Ví dụ: "Anh đang tìm để đầu tư hay mua ở lâu dài ạ?"
  → TRÁNH: giới thiệu dự án, gửi link, nói giá ngay lập tức

B = Xây Dựng Tin Tưởng (đã biết nhu cầu, khách đang đánh giá Bình có đáng tin không)
  → MỤC TIÊU: cho khách thấy Bình hiểu họ và có dữ liệu thật
  → CÁCH: nhận ra cảm xúc/băn khoăn của khách ("Có vẻ anh đang..."), rồi gửi đúng thứ họ cần
  → ĐT: tỷ suất thực tế + track record S1-S3; Ở: tiện ích + căn phù hợp; Hoài Nghi: dữ liệu cụ thể có nguồn
  → TRÁNH: push quyết định, hỏi "anh có muốn book không"

C = Nuôi Dưỡng (đang chần chừ, chưa thấy đủ lý do để tiến)
  → MỤC TIÊU: hiểu rào cản thật sự là gì — không phải đẩy nhanh
  → CÁCH: hỏi thẳng 1 câu mở để khách tự nói ra điều đang vướng ("Anh đang cân nhắc điểm nào nhất ạ?")
  → Nếu khách đã hỏi nhiều thông tin: có thể chia sẻ thực tế thị trường ngắn gọn — đưa số liệu thật rồi để khách tự kết luận, không kết luận thay họ
  → Nếu khách ở/sắp về Đà Nẵng: mời xem thực địa tự nhiên như một lựa chọn, không phải nhiệm vụ
  → TRÁNH: tạo cảm giác cấp bách giả, nói "sắp hết căn", nói "giá sắp tăng" khi chưa có căn cứ

D = Đánh Giá (nghiêm túc, đang so sánh nhiều nơi, cần thông tin cụ thể)
  → MỤC TIÊU: giúp khách có đủ thông tin để so sánh công bằng
  → CÁCH: chủ động nêu điểm yếu/rủi ro trước khi khách hỏi — điều này tạo tin tưởng hơn là che giấu
  → Giải đáp thẳng, không vòng vo; đưa số liệu cụ thể; thừa nhận điểm thua nếu có
  → Ví dụ: "Em nói thẳng luôn: S5 là đất 50 năm — điểm này anh cần cân nhắc kỹ..."
  → TRÁNH: chỉ nói ưu điểm, né câu hỏi khó, so sánh kiểu dìm đối thủ

E = Hỗ Trợ Quyết Định (khách gần quyết, còn 1-2 điểm băn khoăn cuối)
  → MỤC TIÊU: tháo đúng điểm vướng — không tạo thêm áp lực mới
  → CÁCH: thu nhỏ bước tiếp theo thành hành động nhỏ nhất có thể, không rủi ro
  → Ví dụ: "Booking thiện chí 50tr — hoàn 100% nếu anh không ưng giá chính thức, không ràng buộc gì"
  → TRÁNH: dùng ngôn ngữ như khách đã quyết ("khi anh booking..."), tạo deadline giả, nói "sắp hết căn"

F = Dài Hạn (đã booking hoặc đang chăm sóc)
  → MỤC TIÊU: duy trì quan hệ thật, không phải giả vờ quan tâm
  → CÁCH: cập nhật tự nhiên, hỏi thêm nhu cầu, chỉ liên hệ khi có gì mới thực sự
  → TRÁNH: follow-up kiểu "anh/chị ơi đã quyết chưa ạ"

QUY TẮC CHUNG (bắt buộc):
- Mỗi tin nhắn chỉ làm 1 việc — đáp lại điều khách VỪA nói, không nhồi thêm thông tin
- Kỹ thuật tâm lý nhúng vào ngôn ngữ tự nhiên — người đọc không nhận ra là đang bị dẫn dắt
- Không push khi khách chưa cho tín hiệu muốn tiến
- Câu văn như Zalo thật, không corporate
- Mời xem thực địa CHỈ KHI vị trí là Đà Nẵng{location_context}

ĐOẠN CHAT:
{chat_text}

GIỌNG BÌNH (bắt buộc):
- Xưng "em", gọi "{honorific + ' ' if honorific else ''}{customer_name}"
- Bắt đầu bằng "Dạ {honorific + ' ' if honorific else ''}{customer_name} ơi"
- Kết bằng "ạ", "nha" hoặc "nha ạ" — không dùng "nhé", "bạn"
- Tối đa 3 câu, tự nhiên như nhắn Zalo
- Không emoji, không corporate

Trả lời JSON:
{{
  "phase": "A/B/C/D/E/F",
  "customer_type": "ĐT/Ở/Quyết Nhanh/Hoài Nghi",
  "technique": "1 trong: Lắng nghe phản chiếu / Gọi tên cảm xúc / Chia sẻ thực tế / Hỏi rào cản / Minh bạch chủ động / Thu nhỏ bước tiếp / Cập nhật tự nhiên",
  "reason": "lý do 1 câu — vì sao phase + loại khách này",
  "summary": "2-3 câu nhật ký: (1) khách đang ở đâu, (2) loại khách + tín hiệu chính, (3) rào cản hoặc bước tiếp theo. Dùng từ đời thường, không học thuật.",
  "timing": {{
    "should_message": true/false,
    "urgency": "ngay bây giờ / hôm nay / vài ngày nữa / chờ khách phản hồi",
    "reason": "1 câu giải thích ngắn gọn dựa trên trạng thái chat — ví dụ: khách vừa hỏi chưa được trả lời, hoặc tin cuối là của mình chưa có reply nên nên chờ, hoặc khách im 3 ngày phù hợp follow-up nhẹ"
  }}
}}"""

    import time
    for model in [GEMINI_MODEL, GEMINI_FALLBACK]:
        for attempt in range(2):
            try:
                response = gemini.models.generate_content(model=model, contents=prompt)
                text = response.text.strip()
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    return json.loads(match.group())
                return None
            except Exception as e:
                err = str(e)
                if "503" in err or "UNAVAILABLE" in err:
                    time.sleep(1.5)
                    continue
                break  # 429 hoặc lỗi khác → thử model tiếp
    return None

PHASE_RANK = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "": 0}

SCRIPTS_BY_PHASE = {
    "A": [
        {"label": "Chào lần đầu — ngoài giờ",
         "hint": "Chào lần đầu, đề xuất gọi 9h sáng mai",
         "text": "Em chào anh/chị ạ. Em là Bình, môi giới Symphony 5 bên IQI. Em vừa nhận thông tin của anh/chị. Em không gọi giờ này vì sợ làm phiền. Em đề xuất 9h sáng mai em gọi anh/chị 10 phút trao đổi nhanh được không ạ? Nếu giờ đó khó, anh/chị nhắn lại khung giờ tiện hơn em sẽ gọi ạ."},
        {"label": "Chào lần đầu — trong giờ",
         "hint": "Chào lần đầu, xin phép gọi 2 phút ngay hôm nay",
         "text": "Chào anh/chị, em là Bình Phan - IQI Đà Nẵng. Em vừa nhận thông tin anh/chị quan tâm Sun Symphony Residence 5 ạ. Em xin phép gọi anh/chị trong 2 phút để gửi tài liệu phù hợp nhất. Nếu anh/chị đang bận, cho em xin khung giờ tiện hơn trong hôm nay ạ."},
        {"label": "Sau khi gọi — xác nhận gửi tài liệu",
         "hint": "Báo sẽ gửi 3 thứ theo nhịp hôm nay, không làm rối",
         "text": "Em sẽ gửi anh/chị qua Zalo 3 thứ trong hôm nay: vị trí dự án, mặt bằng căn anh/chị quan tâm, và bảng giá đợt đầu. Em gửi theo nhịp để anh/chị xem không bị rối, anh/chị thấy ổn không ạ?"},
        {"label": "Gọi không bắt máy",
         "hint": "Báo đã gọi, gửi ảnh trước, không vội — để khách chủ động",
         "text": "Em gọi anh/chị 2 lần chưa được, chắc đang bận ạ. Em gửi ảnh toàn cảnh Symphony để hình dung trước. Khi nào tiện anh/chị nhắn lại em ạ. Không vội."},
    ],
    "B": [
        {"label": "Gửi vị trí dự án",
         "hint": "Mặt tiền Trần Hưng Đạo, cách cầu Rồng 1.5km, liền kề S1-S3",
         "text": "Anh/chị, em gửi vị trí chi tiết Symphony 5 ạ:\n- Mặt tiền Trần Hưng Đạo, quận Sơn Trà\n- Cách cầu Rồng 1,5km, đi bộ ra bến du thuyền\n- Liền kề Symphony 1, 2, 3 đang vận hành (anh/chị tự kiểm chứng được)"},
        {"label": "Giới thiệu bản thân",
         "hint": "10 năm BĐS, TikTok @binh_phan_bds, không né câu khó",
         "text": "Em giới thiệu lại để anh/chị yên tâm ạ: em làm BĐS 10 năm, hiện ở IQI Đà Nẵng, chuyên Symphony và FourS Tower. TikTok: @binh_phan_bds. Có gì anh/chị cứ hỏi thẳng, em không né câu khó đâu ạ."},
        {"label": "Gửi mặt bằng + gợi ý 2 căn",
         "hint": "Gửi mặt bằng, note 2 căn: view sông vs nội khu chênh 8-12%",
         "text": "Anh/chị xem qua mặt bằng [loại căn] giúp em ạ. Em note nhanh:\n- Căn [X] hướng [Y] view sông trực diện\n- Căn [Z] hướng [W] view nội khu, giá mềm hơn 8-12%\nAnh/chị thấy hợp căn nào để em gửi giá đợt đầu ạ?"},
        {"label": "Gửi phân tích thị trường",
         "hint": "Gửi PDF phân tích — dùng được khi so cả dự án khác",
         "text": "Anh/chị, em gửi 1 PDF tổng hợp từ số liệu Sở Du lịch ĐN và Savills. Em làm cái này không phải để bán Symphony - anh/chị so dự án khác cũng dùng được. Đọc khi rảnh, có gì em làm rõ giúp ạ."},
    ],
    "C": [
        {"label": "Tỷ suất cho thuê S1-S3 thực tế",
         "hint": "Studio 7-8.5%, 1PN+ 8-9.5%/năm — S5 vị trí tốt hơn",
         "text": "Anh/chị, em gửi tỷ suất cho thuê Symphony 1, 2, 3 thực tế:\n- Studio: lấp đầy 72-80%, ròng 7-8.5%/năm\n- 1PN+: ròng 8-9.5%/năm\n- 2PN view sông: ròng 6.5-8%/năm\nSymphony 5 sát sông Hàn, vị trí tốt hơn S1-S3 nên kỳ vọng cao hơn ạ."},
        {"label": "Social proof — khách HN vừa chốt",
         "hint": "Khách HN chọn S5 vì chuỗi S1-S3 đã chứng minh dòng tiền thật",
         "text": "Anh/chị, em vừa chốt 1 anh/chị bên Hà Nội tuần trước - căn 2PN view sông Symphony 5. Anh ấy cũng đắn đo giữa Symphony và 1 dự án Sơn Trà. Lý do chọn S5: chuỗi S1-S3 đã chứng minh dòng tiền cho thuê thật, không phải đoán. Em chia sẻ để anh/chị có thêm góc nhìn thôi ạ."},
        {"label": "Follow-up nhẹ — hỏi còn vướng gì",
         "hint": "Hỏi còn câu nào chưa rõ không, không hối thúc",
         "text": "Dạ anh/chị ơi, Bình đây ạ. Em hỏi thăm anh/chị có vướng câu nào em chưa trả lời rõ không, hoặc đang phân vân điểm gì để em làm rõ giúp ạ."},
        {"label": "Khách không phản hồi — giữ kết nối",
         "hint": "Không làm phiền thêm, để ngỏ — khi cần khách tự nhắn",
         "text": "Anh/chị ơi, em không làm phiền thêm ạ. Khi nào anh/chị cần em sẵn sàng. Nếu không cần nữa cứ nói thẳng em ngừng ạ."},
    ],
    "D": [
        {"label": "Gửi bảng giá",
         "hint": "Gửi bảng giá — booking 50tr hoàn 100% nếu không ưng",
         "text": "Anh/chị, em gửi bảng giá tham khảo đợt 1. Booking thiện chí 50tr, hoàn lại nếu không ký HĐMB. Xu hướng S1-S3: giá đợt 1 mềm hơn giá công bố 5-8%. Anh/chị xem trước, có gì em giải thích ạ."},
        {"label": "Gửi 5 phương thức thanh toán",
         "hint": "5 phương thức: không vay CK 9.75%, có vay CK 5% ân hạn 36T",
         "text": "Anh/chị, em gửi 5 phương thức thanh toán Symphony 5 ạ:\n1. Không vay: CK ~9.75%\n2. Vay ngân hàng: CK ~5%, ân hạn 36 tháng, lãi 0% trong ân hạn\n3. TTS 50%: CK ~7.5%\n4. TTS 70%: CK ~8.5%\n5. TTS 95%: CK ~9%\nAnh/chị cho em biết tình hình vốn để em tính phương án tối ưu ạ."},
        {"label": "Giải thích pháp lý 50 năm",
         "hint": "Nói thẳng: 50 năm hợp pháp, gia hạn được, Airbnb OK",
         "text": "Anh/chị, em nói thẳng điểm 50 năm: hoàn toàn hợp pháp theo Luật Đất đai 2024, sau 50 năm được gia hạn không thu hồi, và đất thương mại được phép Airbnb hợp pháp (đất ở không được). Anh/chị có câu hỏi thêm phần này em giải thích tiếp ạ."},
        {"label": "Mời xem thực địa (ở ĐN)",
         "hint": "Cuối tuần dẫn xem cùng KTS — có 2-3 anh chị cùng đi",
         "text": "Cuối tuần này em có buổi dẫn 2-3 anh chị đi xem thực địa Symphony - em đi cùng KTS bên CĐT. Anh/chị sắp xếp được không ạ?"},
        {"label": "Video call xem căn (ngoài ĐN)",
         "hint": "Video call qua Zalo — đứng tại căn thật, xem góc nào quay góc đó",
         "text": "Nếu chưa sắp xếp vào ĐN được, em làm video call dẫn anh/chị đi 1 vòng qua Zalo - em đứng tại căn thật, anh/chị muốn xem góc nào em quay góc đó. Anh/chị tiện cuối tuần này hay đầu tuần sau ạ?"},
    ],
    "E": [
        {"label": "Quy trình booking 3 bước",
         "hint": "3 bước: chọn căn, ký phiếu, chuyển 50tr vào TK công ty IQI",
         "text": "Em đi qua nhanh 3 việc để anh/chị booking đúng quy trình: (1) chọn căn cụ thể, (2) ký phiếu giữ chỗ, (3) chuyển 50tr vào TK công ty IQI - đại lý F1 của Sun Group, không phải TK cá nhân em. Em ghi rõ STK và tên công ty trên phiếu, anh/chị tự đối chiếu được ạ."},
        {"label": "Hỏi còn vướng gì để tiến",
         "hint": "Hỏi thẳng 1 câu — để khách tự nói ra điểm cuối cùng đang vướng",
         "text": "Anh/chị, em hỏi thẳng: từ những gì em chia sẻ, anh/chị thấy còn điểm nào chưa rõ hoặc chưa ưng không ạ? Em muốn hiểu đúng thay vì đoán."},
        {"label": "Xác nhận sau booking",
         "hint": "Căn đã khóa — xác nhận thông tin, để khách cảm thấy chắc chắn",
         "text": "Anh/chị, em vừa hoàn tất giữ căn với CĐT - căn đã khóa cho anh/chị rồi ạ. Em gửi lại thông tin căn + STK thanh toán để anh/chị lưu tham khảo. Có gì cần em hỗ trợ thêm cứ nhắn ạ."},
    ],
    "F": [
        {"label": "Chạm nhẹ sau thời gian im",
         "hint": "Có cập nhật nhỏ — hỏi có muốn nhận không, không bắt buộc",
         "text": "Anh/chị, Bình đây ạ. Lâu rồi không liên lạc. Em có 1 cập nhật nhỏ về Symphony 5 - anh/chị có muốn em gửi qua không? Không bắt buộc, chỉ hỏi thôi ạ."},
        {"label": "Gửi tài liệu hành trình chủ nhân",
         "hint": "Gửi bộ tài liệu: timeline, contact CĐT, FAQ sau booking",
         "text": "Anh/chị, em vừa gửi qua Zalo bộ tài liệu hành trình chủ nhân Symphony 5 gồm: timeline 24 tháng, contact CĐT và ngân hàng, 10 câu hỏi thường gặp sau booking, quy trình thanh toán đợt 1, mã căn và lịch ký HĐMB. Có gì anh/chị nhắn em ạ."},
    ],
}


PROJECT_CONTEXT = {
    "symphony 5": """DỰ ÁN: Sun Symphony Residence 5 (S5)
- Chủ đầu tư: Sun Property (Sun Group) — track record S1/S2/S3/S4 đang vận hành tốt
- Vị trí: ven sông Hàn, phường An Hải Bắc, quận Sơn Trà — view sông Hàn + cầu Rồng + biển Mỹ Khê
- Loại hình: đất thương mại dịch vụ 50 năm — ĐƯỢC phép Airbnb hợp pháp, gia hạn theo Luật Đất đai 2024
- Tầng: 31 tầng | Bàn giao: dự kiến Q1/2028
- Căn hộ: Studio, 1PN+, 2PN — diện tích 28-87m²
- Giai đoạn: pre-launch, đang nhận booking thiện chí 50tr (hoàn 100% nếu không ưng giá)
- Giá tham khảo (rumor tầng 15, chưa công bố chính thức):
  + Studio ~30m²: Có vay ~2,55-3,05 tỷ | Không vay ~2,42-2,89 tỷ | TTS 95% ~2,13-2,55 tỷ
  + 1PN+ ~45-54m²: Có vay ~3,3-3,68 tỷ | Không vay ~3,13-3,50 tỷ | TTS 95% ~2,76-3,08 tỷ
  + 2PN ~64-87m²: Có vay ~5,5-6,5 tỷ | Không vay ~5,2-6,2 tỷ | TTS 95% ~gần 5 tỷ
- 5 phương thức TT: Không vay CK ~9,75% | Có vay CK ~5% ân hạn 36 tháng lãi 0% | TTS 50%/70%/95%
- Tỷ suất cho thuê dự kiến: Airbnb tối đa ~12%/năm | Dài hạn 6,5-8%/năm
- S1-S3 thực tế: 7-9,5%/năm ròng, lấp đầy 72-80%
- LỢI THẾ SO FOURS: view sông Hàn trực diện, Airbnb yield cao hơn, Sun Group uy tín hơn
- ĐIỂM YẾU SO FOURS: sổ 50 năm (không lâu dài như đất ở), giá 2PN cao hơn FourS""",

    "fours tower": """DỰ ÁN: FourS Tower
- Chủ đầu tư: FourS Group
- Vị trí: trung tâm dự án Riverpolis — ngã tư Quảng Nam & Minh Mạng, phường Hòa Quý — view nội khu + thành phố
- Loại hình: đất ở — SỔ HỒNG LÂU DÀI (vĩnh viễn) — lợi thế pháp lý lớn
- Tầng: 25 tầng | Bàn giao: dự kiến Q1/2028
- Căn hộ: Studio, 1PN, 1PN+, 2PN, 3PN
- Giai đoạn: đã mở bán, còn hàng — giá tốt nhất hiện tại
- Giá tham khảo (tầng thấp, tầng cao +10%):
  + Studio ~30m²: Có vay ~2,3-2,4 tỷ | Không vay ~2,0-2,2 tỷ | TTS 95% ~1,5-1,7 tỷ
  + 1PN+ ~45-54m²: Có vay ~2,83-3,45 tỷ | Không vay ~2,68-3,28 tỷ | TTS 95% ~2,24-2,74 tỷ
  + 2PN ~60-73m²: Có vay ~4,01-5,38 tỷ | Không vay ~3,81-5,11 tỷ | TTS 95% ~3,18-4,27 tỷ
- 5 phương thức TT: Có Vay CK ~5% | Không Vay CK ~9,75% | TTS 50%/70%/95%
- Tỷ suất cho thuê dự kiến: Airbnb tối đa ~8,5%/năm | Dài hạn 6-7,5%/năm (phù hợp cư dân ổn định)
- LỢI THẾ SO SYMPHONY: sổ hồng lâu dài, giá 1PN+/2PN rẻ hơn S5 ~10-20%, đã mở bán có giá chính thức
- ĐIỂM YẾU SO SYMPHONY: không có view sông Hàn, Airbnb yield thấp hơn, chủ đầu tư nhỏ hơn Sun Group""",

    "charmora": """DỰ ÁN: Sun Charmora City (Charmora Onsen 3)
- Chủ đầu tư: Sun Group
- Vị trí: ven sông Tắc, Đà Nẵng
- Loại hình: căn hộ onsen, đất ở
- Đang mở bán: Onsen 3 (5/2026), CSBH03
- Hướng căn: TOP=Bắc, LEFT=Tây (sông Tắc — KHÔNG hợp Đông tứ trạch), RIGHT=Đông, BOTTOM=Nam""",

    "vinhomes": """DỰ ÁN: Vinhomes Hải Vân Bay
- Chủ đầu tư: Vinhomes (Vingroup)
- Vị trí: ven vịnh Hải Vân, Đà Nẵng
- Loại hình: đại đô thị nghỉ dưỡng""",
}

def get_project_context(project: str) -> str:
    """Trả về context dự án từ tên project (fuzzy match)."""
    if not project:
        return ""
    pl = project.lower()
    for key, ctx in PROJECT_CONTEXT.items():
        if key in pl or pl in key:
            return ctx
    return ""

TECHNIQUE_INSTRUCTIONS = {
    "Lắng nghe phản chiếu": "Lặp lại 1-2 từ chính khách vừa dùng, rồi hỏi mở thêm 1 câu. Mục tiêu là khách cảm thấy được nghe — không phải dẫn dắt.",
    "Gọi tên cảm xúc": "Nhận ra trạng thái khách đang có và nói nhẹ ra: 'Có vẻ anh/chị đang...' — không phán xét, không vội giải quyết ngay.",
    "Chia sẻ thực tế": "Cung cấp thông tin thị trường/số liệu thật ngắn gọn, trung lập — để khách tự kết luận, không nói 'vậy nên anh phải...'",
    "Hỏi rào cản": "Hỏi thẳng 1 câu mở để khách tự nói ra điều đang vướng: 'Anh đang cân nhắc điểm nào nhất ạ?' — không đoán thay khách.",
    "Minh bạch chủ động": "Tự nêu điểm yếu hoặc rủi ro của dự án trước khi khách hỏi. Điều này tạo tin tưởng hơn là che giấu — 'Em nói thẳng luôn điểm này...'",
    "Thu nhỏ bước tiếp": "Đề xuất hành động nhỏ nhất, ít rủi ro nhất — nêu rõ không ràng buộc, không mất gì nếu đổi ý. Không dùng ngôn ngữ như khách đã quyết.",
    "Cập nhật tự nhiên": "Liên hệ khi có thông tin mới thực sự — hỏi thêm nhu cầu thay vì hỏi 'đã quyết chưa'. Giữ quan hệ không áp lực.",
}


def rewrite_message(text, customer_name, honorific="", phase="", technique="", customer_type=""):
    """Viết lại ý định thô của Bình thành tin nhắn Zalo, nhúng kỹ thuật tâm lý"""
    h = honorific + " " if honorific else ""
    phase_desc = PHASE_DESCRIPTIONS.get(phase, "")
    ti = TECHNIQUE_INSTRUCTIONS.get(technique, "")
    technique_section = f"\nKỸ THUẬT CẦN NHÚNG ({technique}): {ti}" if ti else ""
    type_section = f"\nLoại khách: {customer_type}" if customer_type else ""
    prompt = f"""Bình Phan, sales BĐS IQI Đà Nẵng, 10 năm kinh nghiệm. Viết lại ý định sau thành tin nhắn Zalo — đúng giọng Bình và nhúng kỹ thuật tâm lý vào tự nhiên.

Ý định: {text}
Khách: {h}{customer_name}{type_section}
Phase: {phase_desc}{technique_section}

Quy tắc: xưng "em", gọi "{h}{customer_name}", bắt đầu "Dạ {h}{customer_name} ơi", kết bằng "ạ"/"nha"/"nha ạ", tối đa 3 câu, tự nhiên như nhắn Zalo, nhúng kỹ thuật không lộ liễu, không emoji, không corporate.

Trả về ONLY tin nhắn."""
    resp = gemini.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return resp.text.strip()


def suggest_reply(messages, customer_name, honorific="", phase="", technique="",
                  customer_type="", airtable_context="", intent="", project=""):
    """Đọc toàn bộ đoạn chat + context, tự gợi ý câu trả lời tiếp theo đúng giọng Bình.
    intent: ý định thô (nếu có) — nếu trống thì tự đoán câu tốt nhất.
    """
    h = honorific + " " if honorific else ""
    call_name = f"{h}{customer_name}".strip()
    phase_desc = PHASE_DESCRIPTIONS.get(phase, "")
    ti = TECHNIQUE_INSTRUCTIONS.get(technique, "")

    chat_text = "\n".join([
        f"{'[Bình]' if m['is_me'] else '[Khách]'}: {m['text']}"
        for m in messages[-25:]
    ])

    project_block = ""
    proj_ctx = get_project_context(project)
    if proj_ctx:
        project_block = f"\n{proj_ctx}\n"

    context_block = ""
    if airtable_context:
        context_block = f"\nLỊCH SỬ TƯƠNG TÁC (Airtable):\n{airtable_context}\n"

    intent_block = ""
    if intent:
        intent_block = f"\nÝ ĐỊNH CỦA BÌNH: {intent}\n(Viết thành câu hoàn chỉnh, đừng thay đổi nội dung ý định này)"

    technique_block = ""
    if ti:
        technique_block = f"\nKỸ THUẬT NÊN NHÚNG ({technique}): {ti}"

    prompt = f"""Mày là Bình Phan — sales BĐS IQI Đà Nẵng, 10 năm kinh nghiệm. Mày đang nhắn Zalo với khách.

THÔNG TIN KHÁCH:
- Tên: {call_name}
- Loại khách: {customer_type or "chưa rõ"}
- Phase hiện tại: {phase_desc}{project_block}{context_block}

ĐOẠN CHAT HIỆN TẠI:
{chat_text}
{intent_block}{technique_block}

NHIỆM VỤ:
Viết 1 tin nhắn Zalo tiếp theo. Mục tiêu: khách cảm giác họ đang tự quyết định theo nhu cầu của mình — không cảm giác bị push hay bị bán.

NGUYÊN TẮC VIẾT (quan trọng hơn kỹ thuật):
- Dùng lại TỪ KHÓA khách vừa nói — không diễn dịch lại bằng từ khác
- Hỏi xin phép trước khi gửi thông tin mới: "Em gửi anh... được không ạ?"
- Nếu có dữ liệu: đưa ra rồi để khách tự kết luận, không kết luận thay họ
- Nếu khách đã nói điều gì quan trọng trước đó: tham chiếu lại ("Anh có nói... nên...")
- Khi gợi ý bước tiếp: đưa 2 lựa chọn để khách cảm giác họ đang chọn, không phải bị dẫn
- Nếu khách chưa cho tín hiệu sẵn sàng: đừng push — hỏi thêm hoặc cung cấp thêm thông tin

QUY TẮC GIỌNG BÌNH:
- Xưng "em", gọi "{call_name}"
- Bắt đầu tự nhiên, không nhất thiết phải "Dạ ơi" nếu đang giữa cuộc trò chuyện
- Kết bằng "ạ", "nha" hoặc "nha ạ" — KHÔNG dùng "nhé", "bạn"
- Tối đa 3 câu ngắn, tự nhiên như Zalo thật
- KHÔNG emoji, KHÔNG corporate, KHÔNG kết luận thay khách
- KHÔNG bịa số liệu, KHÔNG tạo deadline giả, KHÔNG nói "sắp hết căn"

Trả về ONLY tin nhắn, không giải thích."""

    resp = gemini.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return resp.text.strip()


# Thư mục lưu tài liệu theo phase
RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "resources")
for _ph in ["A", "B", "C", "D", "E", "F"]:
    os.makedirs(os.path.join(RESOURCES_DIR, f"phase-{_ph}"), exist_ok=True)

def update_airtable_phase(record_id, phase, summary, phone_note="", current_phase=""):
    """Cập nhật Airtable.
    - phone_note: ghi chú cuộc gọi → luôn lưu, ưu tiên tuyệt đối
    - summary (Zalo): chỉ lưu nếu phase mới > phase hiện tại (tích cực hơn)
    """
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{TABLE_ID}/{record_id}"
    headers = {"Authorization": f"Bearer {AIRTABLE_KEY}", "Content-Type": "application/json"}

    fields = {"Phase": phase}

    if phone_note:
        # Cuộc gọi → luôn ghi đè, thêm prefix 📞
        fields["Nội dung tương tác gần nhất"] = phone_note
    elif summary:
        # Zalo → chỉ ghi đè nếu phase tăng
        if PHASE_RANK.get(phase, 0) > PHASE_RANK.get(current_phase, 0):
            fields["Nội dung tương tác gần nhất"] = summary

    r = requests.patch(url, headers=headers, json={"fields": fields}, params={"typecast": "true"})
    return r.status_code == 200


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logs

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        import urllib.parse, mimetypes, base64
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/files":
            phase = qs.get("phase", ["A"])[0]
            folder = os.path.join(RESOURCES_DIR, f"phase-{phase}")
            files = []
            for fn in sorted(os.listdir(folder)):
                fp = os.path.join(folder, fn)
                if os.path.isfile(fp):
                    mime = mimetypes.guess_type(fn)[0] or "application/octet-stream"
                    with open(fp, "rb") as f:
                        data = base64.b64encode(f.read()).decode()
                    files.append({"name": fn, "mime": mime, "data": data})
            self._send_json(files)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        import urllib.parse, base64
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        parsed_path = urllib.parse.urlparse(self.path).path

        # Route: /suggest → gợi ý câu trả lời dựa vào toàn bộ đoạn chat
        if parsed_path == "/suggest":
            messages = body.get("messages", [])
            customer_name = body.get("customer_name", "").strip()
            honorific = body.get("honorific", "").strip()
            phase = body.get("phase", "").strip()
            technique = body.get("technique", "").strip()
            customer_type = body.get("customer_type", "").strip()
            airtable_context = body.get("airtable_context", "").strip()
            intent = body.get("intent", "").strip()
            project = body.get("project", "").strip()
            if not customer_name or not messages:
                self._send_json({"error": "Thiếu customer_name hoặc messages"})
                return
            try:
                reply = suggest_reply(messages, customer_name, honorific, phase,
                                      technique, customer_type, airtable_context, intent, project)
                self._send_json({"reply": reply})
            except Exception as e:
                self._send_json({"error": str(e)})
            return

        # Route: /rewrite → chỉnh câu văn từ ý định thô
        if parsed_path == "/rewrite":
            text = body.get("text", "").strip()
            customer_name = body.get("customer_name", "").strip()
            honorific = body.get("honorific", "").strip()
            phase = body.get("phase", "").strip()
            technique = body.get("technique", "").strip()
            customer_type = body.get("customer_type", "").strip()
            if not text or not customer_name:
                self._send_json({"error": "Thiếu text hoặc customer_name"})
                return
            try:
                refined = rewrite_message(text, customer_name, honorific, phase, technique, customer_type)
                self._send_json({"refined": refined})
            except Exception as e:
                self._send_json({"error": str(e)})
            return

        # Route: /upload → lưu file tài liệu theo phase
        if parsed_path == "/upload":
            phase = body.get("phase", "A")
            filename = os.path.basename(body.get("filename", "file"))
            data = base64.b64decode(body.get("data", ""))
            folder = os.path.join(RESOURCES_DIR, f"phase-{phase}")
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, filename), "wb") as f:
                f.write(data)
            self._send_json({"ok": True, "filename": filename})
            return

        result = self.process(body)
        self._send_json(result)

    def process(self, body):
        zalo_name = body.get("name", "").strip()
        messages = body.get("messages", [])
        phone_hint = body.get("phone_hint", "").strip()
        timestamp = body.get("timestamp", "").strip()  # "14h25 25/5" từ client
        # Thời gian thực kể từ tin nhắn cuối (giờ) — gửi từ extension nếu có timestamp DOM
        hours_since_last = body.get("hours_since_last", None)  # float hoặc None

        if not zalo_name or not messages:
            return {"error": "Thiếu tên hoặc tin nhắn"}

        # Tách tên thật từ "Dự án + [Loại căn] + Tên"
        customer_name, detected_project = strip_project_prefix(zalo_name)
        apt_type = detect_apt_type(zalo_name)  # "1PN+", "Studio", "" nếu không có

        # 1. Lấy danh sách khách từ Airtable
        customers = get_all_customers()

        # 2. Fuzzy match tên + gợi ý SĐT
        matches = fuzzy_match(zalo_name, customers, phone_hint)

        # 3. Lấy vị trí + giới tính + ghi chú từ match tốt nhất (nếu có)
        top_location = ""
        gender_from_airtable = ""
        airtable_context = ""
        if matches:
            f = matches[0]["record"]["fields"]
            top_location = f.get("Địa chỉ", "") or f.get("Vị trí", "")
            gender_from_airtable = f.get("Giới tính", "").lower()
            airtable_context = f.get("Nội dung tương tác gần nhất", "")

        # 4. Tính tên gọi ngắn + xưng hô để dùng trong prompt
        short_name, honorific_from_zalo = get_calling_name(zalo_name)
        if gender_from_airtable in ("nữ", "female"):
            honorific = "chị"
        elif gender_from_airtable in ("nam", "male"):
            honorific = "anh"
        elif honorific_from_zalo in ("chị", "anh"):
            honorific = honorific_from_zalo
        else:
            honorific = ""
        display_name = f"{honorific.capitalize()} {short_name}".strip() if honorific else short_name

        # 5. Phân tích phase — truyền tên gọi ngắn + vị trí + xưng hô + ghi chú Airtable
        analysis = analyze_phase(messages, short_name, top_location, honorific, airtable_context)
        if not analysis:
            return {"error": "Không phân tích được phase"}

        phase = analysis["phase"]
        shortcuts = NEXT_STEP_SHORTCUTS.get(phase, [])

        raw_summary = analysis.get("summary", "")
        prefix = " ".join(filter(None, [timestamp, f"[Phase {phase}]"]))
        summary = f"{prefix} {raw_summary}".strip()

        # 6. Timing: phase-aware hardcoded rules override AI timing
        call_name = f"{honorific} {short_name}".strip() if honorific else short_name

        # Phát hiện "cuộc trò chuyện đang active" — khách đã reply lại sau khi từng im
        # Active = tin cuối là của khách HOẶC có trao đổi 2 chiều trong 6 tin gần nhất
        def conversation_is_active(msgs):
            if not msgs:
                return False
            if not msgs[-1].get("is_me"):
                return True  # tin cuối là của khách
            recent = msgs[-6:]
            has_customer = any(not m.get("is_me") for m in recent)
            has_me = any(m.get("is_me") for m in recent)
            return has_customer and has_me  # có trao đổi 2 chiều gần đây

        # Dùng tên đầy đủ từ Airtable làm tiêu đề lịch — fallback về call_name
        airtable_full_name = matches[0]["record"]["fields"].get("Tên", "") if matches else ""
        event_display_name = airtable_full_name if airtable_full_name else call_name

        calendar_deleted = False
        calendar_saved = False

        # Nếu khách đang trò chuyện lại → xóa event follow-up cũ (nếu có)
        if _load_reminders().get(call_name) and conversation_is_active(messages):
            calendar_deleted = delete_reminder_for_customer(call_name)

        hardcoded = detect_timing_rules(messages, phase=phase, hours_since_last=hours_since_last, project=detected_project)
        if hardcoded:
            timing_final = hardcoded
            wait_days = hardcoded.get("wait_days", 2)
            follow_hour = hardcoded.get("follow_up_hour", 19)
            reason = hardcoded.get("reason", "")
        else:
            cfg = PHASE_TIMING.get(phase, PHASE_TIMING["C"])
            think_days, think_hour = cfg[0], cfg[1]
            timing_final = analysis.get("timing", {})
            wait_days = think_days
            follow_hour = think_hour
            reason = timing_final.get("reason") or f"Không có tín hiệu đặc biệt — follow-up mặc định theo Phase {phase}"
            timing_final["wait_days"] = wait_days
            timing_final["follow_up_hour"] = follow_hour
            timing_final["reason"] = reason

        # Dedup: chỉ tạo event mới nếu chưa có event cùng ngày cho khách này
        target_date = (datetime.now() + timedelta(days=wait_days)).date().isoformat()
        existing_entry = _load_reminders().get(call_name)
        if existing_entry and existing_entry.get("target_date") == target_date:
            print(f"Calendar: event already exists for {call_name} on {target_date}, skipping", flush=True)
        else:
            if existing_entry:
                delete_reminder_for_customer(call_name)
            calendar_saved = create_calendar_event(call_name, event_display_name, wait_days, follow_hour, reason)

        timing_final["calendar_saved"] = calendar_saved
        timing_final["calendar_deleted"] = calendar_deleted

        return {
            "phase": phase,
            "phase_desc": PHASE_DESCRIPTIONS.get(phase, ""),
            "customer_type": analysis.get("customer_type", ""),
            "technique": analysis.get("technique", ""),
            "reason": analysis.get("reason", ""),
            "summary": summary,
            "apt_type": apt_type,
            "shortcuts": shortcuts,
            "scripts": SCRIPTS_BY_PHASE.get(phase, []),
            "honorific": honorific,
            "short_name": short_name,
            "project": detected_project,
            "timing": timing_final,
            "matches": [
                {
                    "id": m["record"]["id"],
                    "name": m["name"],
                    "score": round(m["score"], 2),
                    "project": m["record"]["fields"].get("Dự án quan tâm", ""),
                    "status": m["record"]["fields"].get("Trạng thái", ""),
                    "location": m["record"]["fields"].get("Địa chỉ", "") or m["record"]["fields"].get("Vị trí", ""),
                    "phase": m["record"]["fields"].get("Phase", ""),
                }
                for m in matches
            ]
        }

    def do_PATCH(self):
        """Cập nhật Airtable sau khi user xác nhận khách"""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        record_id = body.get("record_id")
        phase = body.get("phase", "")
        summary = body.get("summary", "")
        phone_note = body.get("phone_note", "").strip()
        current_phase = body.get("current_phase", "")

        ok = update_airtable_phase(record_id, phase, summary, phone_note, current_phase)
        self._send_json({"ok": ok})


if __name__ == "__main__":
    port = 7788
    print(f"✅ Zalo Assistant Server đang chạy tại http://localhost:{port}")
    HTTPServer(("localhost", port), Handler).serve_forever()
