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
        "fields[]": ["Tên", "Dự án quan tâm", "Hành động tiếp theo", "Số lần liên hệ",
                     "Phase", "Nội dung tương tác gần nhất", "Kết quả gần nhất"],
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


# Mục đích cụ thể cho mỗi lần liên hệ — thêm giá trị, không hỏi "đã quyết chưa"
CONTACT_PURPOSE = {
    1: {
        "label": "Kết nối lần đầu",
        "guide": "Hỏi thăm đã nhận SMS chưa. Hỏi 1 câu mở để hiểu nhu cầu — chưa giới thiệu dự án.",
        "vi_du": "\"Anh nhận được tin em chưa ạ? Anh đang tìm hiểu để đầu tư hay mua ở lâu dài?\"",
    },
    2: {
        "label": "Gửi thông tin có giá trị",
        "guide": "Chia sẻ 1 thông tin cụ thể phù hợp nhu cầu — tỷ suất, pháp lý, mặt bằng. Hỏi xin phép trước khi gửi.",
        "vi_du": "\"Em có tài liệu tỷ suất thực tế S1-S3 — anh muốn em gửi qua không ạ?\"",
    },
    3: {
        "label": "Hỏi thẳng rào cản",
        "guide": "Hỏi 1 câu mở để khách tự nói ra điều đang vướng. Không đoán thay khách.",
        "vi_du": "\"Anh đang cân nhắc điểm nào nhất ạ? Em muốn hiểu đúng thay vì đoán.\"",
    },
    4: {
        "label": "Chạm nhẹ — để ngỏ",
        "guide": "Không hỏi quyết định. Chia sẻ 1 cập nhật mới nếu có, hoặc chỉ cho biết em vẫn ở đây khi cần.",
        "vi_du": "\"Anh ơi, em không làm phiền thêm. Khi nào anh cần em sẵn sàng, cứ nhắn ạ.\"",
    },
}

# Gợi ý thêm theo Phase của khách
PHASE_HINT = {
    "A": "Khách mới — ưu tiên lắng nghe, chưa vội giới thiệu dự án.",
    "B": "Đang xây dựng tin tưởng — gửi dữ liệu thật, để khách tự đánh giá.",
    "C": "Đang chần chừ — hỏi rào cản thật sự, không tạo thêm áp lực.",
    "D": "Đang so sánh — minh bạch cả ưu điểm lẫn hạn chế, khách tự kết luận.",
    "E": "Gần quyết — thu nhỏ bước tiếp thành hành động nhỏ nhất, không rủi ro.",
    "F": "Dài hạn — chỉ liên hệ khi có cập nhật thật, không hỏi \"đã quyết chưa\".",
}

def format_record(rec, prefix=""):
    f       = rec.get("fields", {})
    name    = f.get("Tên", "Không rõ")
    project = f.get("Dự án quan tâm", "")
    action  = f.get("Hành động tiếp theo", "").strip()
    lan     = f.get("Số lần liên hệ")
    phase   = f.get("Phase", "").strip()
    ket_qua = f.get("Kết quả gần nhất", "").strip()

    lan_int = int(lan) if lan else 0
    lan_tag = f" [Lần {lan_int}]" if lan_int else ""
    line = f"{prefix}<b>{name}</b>{lan_tag}"
    if project:
        line += f" · {project}"
    if phase:
        line += f" · Phase {phase}"

    # Kết quả lần trước (nếu có)
    if ket_qua:
        line += f"\n    📝 Lần trước: {ket_qua}"

    # Hành động Bình đã set thủ công trong Airtable (nếu có)
    if action:
        line += f"\n    ✅ {action}"

    # Gợi ý mục đích lần liên hệ này
    purpose = CONTACT_PURPOSE.get(lan_int)
    if purpose:
        line += f"\n    💡 <b>{purpose['label']}:</b> {purpose['guide']}"
        line += f"\n    <i>{purpose['vi_du']}</i>"

    # Gợi ý thêm theo phase
    phase_hint = PHASE_HINT.get(phase)
    if phase_hint:
        line += f"\n    <i>Phase {phase}: {phase_hint}</i>"

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
