#!/usr/bin/env python3
"""
Telegram Daemon — Nhận lệnh từ Telegram, xử lý bằng Claude, trả lời về Telegram.

Chạy ngầm trên Mac:
    python3 scripts/telegram_daemon.py

Dừng: Ctrl+C hoặc kill process

Các lệnh hỗ trợ (ngôn ngữ tự nhiên):
    - Thêm bài vào lịch
    - Xem lịch hôm nay / tuần này
    - Trạng thái bài đăng
    - Đăng bài thủ công
    - Câu hỏi về thị trường BĐS
    - /reset — xoá lịch sử hội thoại
"""

import base64
import json
import os
import sys
import time
import traceback
import requests
from pathlib import Path
from datetime import datetime, timedelta

# ── Config ────────────────────────────────────────────────────────────────────

WORKSPACE = Path(__file__).parent.parent

def load_env():
    env = {}
    for line in (WORKSPACE / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    env.update({k: v for k, v in os.environ.items() if v})
    return env

ENV = load_env()

TELEGRAM_TOKEN   = ENV["TELEGRAM_BOT_TOKEN"]
AUTHORIZED_CHAT  = int(ENV["TELEGRAM_CHAT_ID"])
ANTHROPIC_KEY    = ENV["ANTHROPIC_API_KEY"]
AIRTABLE_KEY     = ENV["AIRTABLE_API_KEY"]
AIRTABLE_BASE    = ENV["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE   = "tbll5ikhBQPeak8xR"
AT_KH_TABLE      = "tblf9ibYWQ8Q4viBt"   # Khách Hàng
AT_CSKH_TABLE    = "tblOU5r9U7qZBpjvP"   # Lịch Sử CSKH

TG_BASE    = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
AT_HEADERS = {"Authorization": f"Bearer {AIRTABLE_KEY}", "Content-Type": "application/json"}
AT_URL     = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}"
AT_KH_URL  = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{AT_KH_TABLE}"
AT_CSKH_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{AT_CSKH_TABLE}"

OFFSET_FILE    = WORKSPACE / "outputs" / ".tg_offset"
CONV_TIMEOUT   = 5 * 60    # xoá history sau 5 phút không hoạt động
MAX_HISTORY    = 10        # giữ tối đa 5 exchanges (5 user + 5 assistant)

# ── Conversation memory ───────────────────────────────────────────────────────

# {chat_id: {"messages": [...], "last_active": float}}
conversations: dict = {}

def get_history(chat_id: int) -> list:
    now = time.time()
    if chat_id not in conversations:
        conversations[chat_id] = {"messages": [], "last_active": now}
        return conversations[chat_id]["messages"]
    conv = conversations[chat_id]
    if now - conv["last_active"] > CONV_TIMEOUT:
        conv["messages"] = []
        print(f"[{datetime.now().strftime('%H:%M:%S')}] History expired, reset for {chat_id}")
    conv["last_active"] = now
    return conv["messages"]

def append_exchange(chat_id: int, user_content, assistant_text: str):
    """Lưu 1 cặp user/assistant vào history. Trim nếu quá dài."""
    msgs = conversations[chat_id]["messages"]
    msgs.append({"role": "user",      "content": user_content})
    msgs.append({"role": "assistant", "content": assistant_text})
    if len(msgs) > MAX_HISTORY:
        conversations[chat_id]["messages"] = msgs[-MAX_HISTORY:]

def reset_history(chat_id: int):
    if chat_id in conversations:
        conversations[chat_id]["messages"] = []


# ── Telegram helpers ──────────────────────────────────────────────────────────

def tg_send(chat_id: int, text: str, parse_mode="Markdown"):
    try:
        requests.post(f"{TG_BASE}/sendMessage", json={
            "chat_id": chat_id, "text": text, "parse_mode": parse_mode
        }, timeout=10)
    except Exception:
        # Fallback: gửi không parse_mode nếu Markdown lỗi
        try:
            requests.post(f"{TG_BASE}/sendMessage", json={
                "chat_id": chat_id, "text": text
            }, timeout=10)
        except Exception:
            pass

def tg_get_updates(offset: int):
    r = requests.get(f"{TG_BASE}/getUpdates", params={
        "offset": offset, "timeout": 30, "allowed_updates": ["message"]
    }, timeout=40)
    return r.json().get("result", [])

def tg_download_photo(file_id: str):
    """Tải ảnh từ Telegram về, trả về bytes."""
    try:
        r = requests.get(f"{TG_BASE}/getFile", params={"file_id": file_id}, timeout=10)
        file_path = r.json()["result"]["file_path"]
        r2 = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}", timeout=30)
        return r2.content
    except Exception as e:
        print(f"[WARN] tg_download_photo failed: {e}")
        return None

def load_offset() -> int:
    if OFFSET_FILE.exists():
        return int(OFFSET_FILE.read_text().strip())
    return 0

def save_offset(offset: int):
    OFFSET_FILE.write_text(str(offset))

# ── Airtable tools ────────────────────────────────────────────────────────────

def airtable_get_schedule(days_ahead: int = 7) -> list:
    today = datetime.now()
    records = []
    for i in range(days_ahead + 1):
        date = (today + timedelta(days=i)).strftime("%d/%m/%Y")
        r = requests.get(AT_URL, headers=AT_HEADERS, params={
            "filterByFormula": f"FIND('{date}', {{Đăng lúc}}) > 0",
            "fields[]": ["Số bài", "Tiêu đề", "Status", "Đăng lúc", "Format", "Platform", "Slug"]
        })
        records.extend(r.json().get("records", []))
    return records

def airtable_add_draft(title: str, scheduled_date: str, format_type: str,
                       theme: str, platform: list, notes: str = "") -> dict:
    r = requests.get(AT_URL, headers=AT_HEADERS, params={
        "fields[]": ["Số bài"], "sort[0][field]": "Số bài", "sort[0][direction]": "desc", "pageSize": 1
    })
    recs = r.json().get("records", [])
    next_num = (recs[0]["fields"].get("Số bài", 0) + 1) if recs else 1
    slug = f"{next_num:03d}-{title.lower()[:30].replace(' ', '-').replace('/', '-')}"

    fields = {
        "Số bài":   next_num,
        "Tiêu đề":  title,
        "Slug":     slug,
        "Status":   "Draft",
        "Đăng lúc": scheduled_date,
        "Format":   format_type,
        "Platform": platform,
    }
    if notes:
        fields["Ghi chú"] = notes

    r2 = requests.post(AT_URL, headers=AT_HEADERS, json={"fields": fields})
    return r2.json()

def airtable_trigger_event(event_description: str) -> str:
    """
    Tìm tất cả khách Chờ sự kiện, tạo lịch CSKH follow-up lần 1 từ ngày mai,
    trả về danh sách để Bình biết cần chăm sóc ai.
    """
    from datetime import date, timedelta
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Lấy khách Chờ sự kiện
    r = requests.get(AT_KH_URL, headers=AT_HEADERS, params={
        "filterByFormula": "{Trạng thái}='Chờ sự kiện'",
        "fields[]": ["Tên", "Dự án quan tâm", "Ghi chú"],
        "pageSize": 100,
    })
    customers = r.json().get("records", [])
    if not customers:
        return "Không có khách nào đang ở trạng thái Chờ sự kiện."

    # Tạo CSKH lần 1 cho từng khách (batch 10)
    new_records = []
    for c in customers:
        f = c["fields"]
        new_records.append({"fields": {
            "Khách hàng": f.get("Tên", ""),
            "Dự án đề cập": f.get("Dự án quan tâm", ""),
            "Hình thức": "Zalo",
            "Hành động tiếp theo": f"Sự kiện: {event_description}. Lần 1 — liên hệ lại và gửi thông tin mới.",
            "Ngày follow-up": tomorrow,
        }})

    for i in range(0, len(new_records), 10):
        batch = new_records[i:i+10]
        requests.post(AT_CSKH_URL, headers=AT_HEADERS,
                      json={"records": batch, "typecast": True})

    # Cập nhật trạng thái sang Đang chăm sóc
    ids = [c["id"] for c in customers]
    for i in range(0, len(ids), 10):
        batch = [{"id": rid, "fields": {"Trạng thái": "Đang chăm sóc"}} for rid in ids[i:i+10]]
        requests.patch(AT_KH_URL, headers=AT_HEADERS,
                       json={"records": batch, "typecast": True})

    names = [c["fields"].get("Tên", "?") for c in customers]
    return (f"Đã kích hoạt follow-up cho {len(customers)} khách: {', '.join(names)}.\n"
            f"Lịch lần 1 đặt vào ngày mai ({tomorrow}). "
            f"Telegram sẽ nhắc Bình lúc 8:30 sáng.")


def airtable_get_today() -> list:
    today = datetime.now().strftime("%d/%m/%Y")
    r = requests.get(AT_URL, headers=AT_HEADERS, params={
        "filterByFormula": f"FIND('{today}', {{Đăng lúc}}) > 0",
        "fields[]": ["Số bài", "Tiêu đề", "Status", "Đăng lúc", "Format", "Slug"]
    })
    return r.json().get("records", [])

# ── Claude API ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""Bạn là trợ lý content cho Bình Phan — môi giới BĐS IQI Đà Nẵng, 10 năm kinh nghiệm.
Ngày hôm nay: {datetime.now().strftime('%d/%m/%Y')}.

Workspace: hệ thống tạo và đăng nội dung Facebook/TikTok/Instagram về BĐS Đà Nẵng.
Dự án đang phân phối: Sun Symphony Residence 5, Vinhomes Hải Vân Bay, FourS Tower.
Tệp khán giả: nhà đầu tư, người mua nhà ở Đà Nẵng và toàn quốc.

Bạn có thể thực hiện các actions sau qua function calling:
- get_today_schedule: xem lịch đăng hôm nay
- get_week_schedule: xem lịch đăng tuần này
- add_post_to_schedule: thêm bài vào lịch
- trigger_event_followup: khi Bình báo có sự kiện mới (FourS F2/F3 mở bán, dự án mới, có giá chính thức...) thì kích hoạt follow-up cho tất cả khách Chờ sự kiện

Lịch đăng đa kênh (BMN/TikTok/IG/Threads) chỉ có 2 slot hợp lệ:
- 08:00 — bài chính (Carousel hoặc Ảnh + story)
- 18:00 — bài phụ (Infographic hoặc Ảnh cảnh)
Không lên lịch ở các giờ khác (12:00, 21:00... đã bỏ).

Khi nhận được yêu cầu thêm lịch, hãy:
1. Phân tích ngày từ text (ví dụ "thứ 3 tới" = ngày cụ thể, dựa vào ngày hôm nay)
2. Hỏi Bình muốn slot 08:00 hay 18:00 nếu không nói rõ
3. Xác định format phù hợp (Ảnh cá nhân / Carousel / Infographic / AI Infographic)
4. Xác định platform: BMN luôn có; TikTok chỉ khi Carousel slot 08:00; IG+Threads khi slot 18:00
5. Gọi function add_post_to_schedule

Khi người dùng gửi ảnh, hãy phân tích và mô tả ảnh, đồng thời gợi ý cách dùng cho content.

Trả lời ngắn gọn bằng tiếng Việt. Xưng "Bình" khi cần, gọi user là "anh/bạn"."""

TOOLS = [
    {
        "name": "get_today_schedule",
        "description": "Lấy danh sách bài đăng hôm nay",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_week_schedule",
        "description": "Lấy danh sách bài đăng trong 7 ngày tới",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "trigger_event_followup",
        "description": "Khi có sự kiện mới (dự án mở bán, thông tin mới...), kích hoạt follow-up cho tất cả khách đang Chờ sự kiện",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_description": {"type": "string", "description": "Mô tả sự kiện, ví dụ: FourS F2 F3 mở bán, Symphony 5 có giá chính thức"}
            },
            "required": ["event_description"]
        }
    },
    {
        "name": "add_post_to_schedule",
        "description": "Thêm bài mới vào lịch đăng (tạo draft trong Airtable)",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":          {"type": "string",  "description": "Tiêu đề/chủ đề bài"},
                "scheduled_date": {"type": "string",  "description": "Ngày giờ đăng, format DD/MM/YYYY HH:MM"},
                "format_type":    {"type": "string",  "enum": ["Ảnh cá nhân", "Carousel", "Infographic"], "description": "Định dạng bài"},
                "theme":          {"type": "string",  "enum": ["cá nhân", "thị trường", "dự án", "nghề", "đầu tư"], "description": "Chủ đề"},
                "platform":       {"type": "array",   "items": {"type": "string"}, "description": "Danh sách platform: Facebook BMN, Facebook IQI, TikTok, Instagram, Threads"},
                "notes":          {"type": "string",  "description": "Ghi chú thêm (tuỳ chọn)"}
            },
            "required": ["title", "scheduled_date", "format_type", "theme", "platform"]
        }
    }
]


def run_tool(name: str, inputs: dict) -> str:
    if name == "get_today_schedule":
        records = airtable_get_today()
        if not records:
            return "Hôm nay không có bài nào được lên lịch."
        lines = [f"📅 Lịch hôm nay ({datetime.now().strftime('%d/%m/%Y')}):"]
        for rec in sorted(records, key=lambda x: x["fields"].get("Đăng lúc", "")):
            f = rec["fields"]
            icon = "✅" if f.get("Status") == "Published" else "⏳"
            lines.append(f"{icon} {f.get('Đăng lúc','?')} — #{f.get('Số bài','?')} {f.get('Tiêu đề','?')} [{f.get('Format','?')}]")
        return "\n".join(lines)

    elif name == "get_week_schedule":
        records = airtable_get_schedule(7)
        if not records:
            return "Không có bài nào trong 7 ngày tới."
        records.sort(key=lambda x: x["fields"].get("Đăng lúc", ""))
        lines = ["📅 Lịch 7 ngày tới:"]
        for rec in records:
            f = rec["fields"]
            icon = "✅" if f.get("Status") == "Published" else "⏳" if f.get("Status") == "Scheduled" else "📝"
            lines.append(f"{icon} {f.get('Đăng lúc','?')} — {f.get('Tiêu đề','?')} [{f.get('Format','?')}]")
        return "\n".join(lines)

    elif name == "trigger_event_followup":
        return airtable_trigger_event(inputs.get("event_description", ""))

    elif name == "add_post_to_schedule":
        result = airtable_add_draft(
            title          = inputs["title"],
            scheduled_date = inputs["scheduled_date"],
            format_type    = inputs["format_type"],
            theme          = inputs["theme"],
            platform       = inputs["platform"],
            notes          = inputs.get("notes", "")
        )
        if "id" in result:
            slug = result.get("fields", {}).get("Slug", "?")
            num  = result.get("fields", {}).get("Số bài", "?")
            return f"✅ Đã thêm vào lịch:\n• Bài #{num}: {inputs['title']}\n• Ngày: {inputs['scheduled_date']}\n• Format: {inputs['format_type']}\n• Slug: {slug}"
        return f"❌ Lỗi thêm lịch: {result}"

    return f"Tool '{name}' không tìm thấy."


def ask_claude(chat_id: int, user_content) -> str:
    """
    user_content: str (text) hoặc list (content blocks với ảnh)
    Dùng history của chat_id, append kết quả vào history sau khi xong.
    """
    history = get_history(chat_id)
    # Xây messages = history cũ + tin nhắn mới
    messages = list(history) + [{"role": "user", "content": user_content}]

    final_reply = "✅ Xong."

    for _ in range(5):
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model":      "claude-haiku-4-5-20251001",
                "max_tokens": 1024,
                "system":     SYSTEM_PROMPT,
                "tools":      TOOLS,
                "messages":   messages
            },
            timeout=30
        )
        resp = r.json()

        if resp.get("stop_reason") == "end_turn":
            for block in resp.get("content", []):
                if block.get("type") == "text":
                    final_reply = block["text"]
                    break
            # Lưu exchange vào history (chỉ lưu user + text reply, không lưu tool calls)
            append_exchange(chat_id, user_content, final_reply)
            return final_reply

        if resp.get("stop_reason") == "tool_use":
            tool_results = []
            for block in resp.get("content", []):
                if block.get("type") == "tool_use":
                    tool_output = run_tool(block["name"], block.get("input", {}))
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block["id"],
                        "content":     tool_output
                    })
            messages.append({"role": "assistant", "content": resp["content"]})
            messages.append({"role": "user",      "content": tool_results})
            continue

        error = resp.get("error", {})
        return f"❌ Lỗi Claude API: {error.get('message', str(resp))}"

    return "❌ Timeout sau 5 vòng xử lý."


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    print(f"🤖 Telegram daemon started — listening for chat_id {AUTHORIZED_CHAT}")
    print(f"   Workspace: {WORKSPACE}")
    print("   /reset để xoá history | Ctrl+C để dừng\n")

    offset = load_offset()

    while True:
        try:
            updates = tg_get_updates(offset)

            for update in updates:
                offset = update["update_id"] + 1
                save_offset(offset)

                msg     = update.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                if chat_id != AUTHORIZED_CHAT:
                    continue

                text    = (msg.get("text") or msg.get("caption") or "").strip()
                photos  = msg.get("photo")

                # /reset command
                if text == "/reset":
                    reset_history(chat_id)
                    tg_send(chat_id, "🔄 Đã xoá lịch sử hội thoại.")
                    continue

                # Bỏ qua nếu không có text lẫn ảnh
                if not text and not photos:
                    continue

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Nhận: {text[:60] or '[ảnh]'}")

                tg_send(chat_id, "⏳ Đang xử lý...")

                try:
                    if photos:
                        # Tải ảnh lớn nhất
                        file_id    = photos[-1]["file_id"]
                        img_bytes  = tg_download_photo(file_id)

                        if img_bytes:
                            img_b64    = base64.standard_b64encode(img_bytes).decode()
                            # Đoán mime type từ magic bytes
                            mime = "image/jpeg"
                            if img_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                                mime = "image/png"

                            # Xây content block: ảnh + caption (nếu có)
                            content_blocks = [
                                {"type": "image", "source": {
                                    "type": "base64", "media_type": mime, "data": img_b64
                                }}
                            ]
                            if text:
                                content_blocks.append({"type": "text", "text": text})
                            else:
                                content_blocks.append({"type": "text", "text": "Bạn thấy ảnh này thế nào? Có phù hợp dùng cho post nào không?"})

                            reply = ask_claude(chat_id, content_blocks)
                        else:
                            reply = "❌ Không tải được ảnh, thử lại sau."
                    else:
                        reply = ask_claude(chat_id, text)

                except Exception as e:
                    reply = f"❌ Lỗi xử lý: {e}"
                    traceback.print_exc()

                tg_send(chat_id, reply)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Trả lời: {reply[:60]}")

        except KeyboardInterrupt:
            print("\n👋 Daemon dừng.")
            sys.exit(0)
        except Exception as e:
            print(f"[ERROR] {e}")
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    main()
