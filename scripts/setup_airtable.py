#!/usr/bin/env python3
"""
Airtable Workspace Setup — Bình Phan BĐS
Tạo toàn bộ base, bảng, fields và import posts hiện có.
"""

import os
import sys
import json
import re
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("AIRTABLE_API_KEY")
if not API_KEY:
    print("❌ AIRTABLE_API_KEY chưa có trong .env")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

META_URL = "https://api.airtable.com/v0/meta"
RECORDS_URL = "https://api.airtable.com/v0"

POSTS_DIR = Path(__file__).parent.parent / "posts"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def api(method, url, **kwargs):
    r = requests.request(method, url, headers=HEADERS, **kwargs)
    if r.status_code not in (200, 201):
        print(f"  ⚠️  {method} {url} → {r.status_code}: {r.text[:300]}")
    return r


def ok(r):
    return r.status_code in (200, 201)


# ─── Create Base ──────────────────────────────────────────────────────────────

def create_base(workspace_id=None):
    """Tạo base mới. Cần workspace_id nếu có nhiều workspace."""
    payload = {"name": "Bình Phan BĐS Workspace"}
    if workspace_id:
        payload["workspaceId"] = workspace_id

    # Tạo với 1 table tạm, sẽ xóa/đổi tên sau
    payload["tables"] = [
        {
            "name": "_setup_temp",
            "fields": [{"name": "Name", "type": "singleLineText"}],
        }
    ]

    r = api("POST", f"{META_URL}/bases", json=payload)
    if ok(r):
        base = r.json()
        print(f"✅ Đã tạo base: {base['name']} (ID: {base['id']})")
        return base["id"]
    else:
        # Thử list bases để user chọn
        print("⚠️  Không tạo được base mới — kiểm tra scope token.")
        print("   Cần scope: schema.bases:write")
        return None


def list_bases():
    r = api("GET", f"{META_URL}/bases")
    if ok(r):
        return r.json().get("bases", [])
    return []


# ─── Table Schemas ────────────────────────────────────────────────────────────

def posts_table():
    return {
        "name": "📝 Posts",
        "fields": [
            {"name": "Số bài", "type": "number", "options": {"precision": 0}},
            {"name": "Tiêu đề", "type": "singleLineText"},
            {"name": "Hook", "type": "multilineText"},
            {
                "name": "Status",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Draft", "color": "grayLight2"},
                        {"name": "Chờ duyệt", "color": "yellowLight2"},
                        {"name": "Approved", "color": "blueLight2"},
                        {"name": "Scheduled", "color": "purpleLight2"},
                        {"name": "Published", "color": "greenLight2"},
                    ]
                },
            },
            {
                "name": "Platform",
                "type": "multipleSelects",
                "options": {
                    "choices": [
                        {"name": "Facebook BMN", "color": "blueLight2"},
                        {"name": "Facebook IQI", "color": "blueBright2"},
                        {"name": "TikTok", "color": "pinkLight2"},
                        {"name": "Instagram", "color": "orangeLight2"},
                        {"name": "YouTube", "color": "redLight2"},
                    ]
                },
            },
            {
                "name": "Phương pháp",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Viral Replication", "color": "purpleLight2"},
                        {"name": "Trend Surfing", "color": "tealLight2"},
                        {"name": "Pain Point", "color": "orangeLight2"},
                    ]
                },
            },
            {
                "name": "Format",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Ảnh cá nhân", "color": "blueLight2"},
                        {"name": "AI Infographic", "color": "greenLight2"},
                        {"name": "Carousel", "color": "yellowLight2"},
                    ]
                },
            },
            {"name": "Ngày tạo", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "Ngày đăng", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "Slug", "type": "singleLineText"},
            {"name": "Dự án liên quan", "type": "singleLineText"},
            {"name": "Likes", "type": "number", "options": {"precision": 0}},
            {"name": "Comments", "type": "number", "options": {"precision": 0}},
            {"name": "Shares", "type": "number", "options": {"precision": 0}},
            {"name": "Ghi chú", "type": "multilineText"},
        ],
    }


def customers_table():
    return {
        "name": "👥 Khách Hàng",
        "fields": [
            {"name": "Tên", "type": "singleLineText"},
            {"name": "Số điện thoại", "type": "phoneNumber"},
            {"name": "Email", "type": "email"},
            {
                "name": "Nguồn",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "TikTok", "color": "pinkLight2"},
                        {"name": "Facebook", "color": "blueLight2"},
                        {"name": "Referral", "color": "greenLight2"},
                        {"name": "Cold Call", "color": "grayLight2"},
                        {"name": "Walk-in", "color": "yellowLight2"},
                        {"name": "Zalo", "color": "tealLight2"},
                        {"name": "Khác", "color": "grayLight2"},
                    ]
                },
            },
            {"name": "Dự án quan tâm", "type": "singleLineText"},
            {
                "name": "Ngân sách",
                "type": "currency",
                "options": {"precision": 0, "symbol": "₫"},
            },
            {
                "name": "Trạng thái",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "New Lead", "color": "blueLight2"},
                        {"name": "Đã liên hệ", "color": "yellowLight2"},
                        {"name": "Đang xem nhà", "color": "orangeLight2"},
                        {"name": "Đang đàm phán", "color": "purpleLight2"},
                        {"name": "Đã chốt", "color": "greenLight2"},
                        {"name": "Nurturing", "color": "tealLight2"},
                        {"name": "Cold", "color": "grayLight2"},
                    ]
                },
            },
            {
                "name": "Ngày tiếp xúc đầu",
                "type": "date",
                "options": {"dateFormat": {"name": "iso"}},
            },
            {
                "name": "Follow-up tiếp theo",
                "type": "date",
                "options": {"dateFormat": {"name": "iso"}},
            },
            {"name": "Địa chỉ", "type": "singleLineText"},
            {"name": "Ghi chú", "type": "multilineText"},
            {"name": "Zalo", "type": "singleLineText"},
        ],
    }


def projects_table():
    return {
        "name": "🏗️ Dự Án",
        "fields": [
            {"name": "Tên dự án", "type": "singleLineText"},
            {"name": "Chủ đầu tư", "type": "singleLineText"},
            {"name": "Vị trí", "type": "singleLineText"},
            {
                "name": "Trạng thái",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Sắp mở bán", "color": "yellowLight2"},
                        {"name": "Đang mở bán", "color": "greenLight2"},
                        {"name": "Đã bàn giao", "color": "blueLight2"},
                        {"name": "Đang xây", "color": "orangeLight2"},
                    ]
                },
            },
            {
                "name": "Giá từ (tỷ)",
                "type": "number",
                "options": {"precision": 2},
            },
            {
                "name": "Giá đến (tỷ)",
                "type": "number",
                "options": {"precision": 2},
            },
            {
                "name": "Ngày bàn giao",
                "type": "date",
                "options": {"dateFormat": {"name": "iso"}},
            },
            {"name": "Website", "type": "url"},
            {"name": "Loại hình", "type": "singleLineText"},
            {"name": "Tổng số căn", "type": "number", "options": {"precision": 0}},
            {"name": "Pháp lý", "type": "singleLineText"},
            {"name": "Slug context", "type": "singleLineText"},
            {"name": "Ghi chú", "type": "multilineText"},
        ],
    }


def schedule_table():
    return {
        "name": "📅 Lịch Làm Việc",
        "fields": [
            {"name": "Tên công việc", "type": "singleLineText"},
            {
                "name": "Loại",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Gặp khách", "color": "blueLight2"},
                        {"name": "Xem dự án", "color": "greenLight2"},
                        {"name": "Follow-up", "color": "yellowLight2"},
                        {"name": "Tạo content", "color": "purpleLight2"},
                        {"name": "Meeting nội bộ", "color": "tealLight2"},
                        {"name": "Hành chính", "color": "grayLight2"},
                        {"name": "Training", "color": "orangeLight2"},
                    ]
                },
            },
            {
                "name": "Độ ưu tiên",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Cao", "color": "redLight2"},
                        {"name": "Trung bình", "color": "yellowLight2"},
                        {"name": "Thấp", "color": "grayLight2"},
                    ]
                },
            },
            {"name": "Khách hàng", "type": "singleLineText"},
            {
                "name": "Ngày",
                "type": "date",
                "options": {"dateFormat": {"name": "iso"}},
            },
            {"name": "Giờ bắt đầu", "type": "singleLineText"},
            {"name": "Địa điểm", "type": "singleLineText"},
            {
                "name": "Trạng thái",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Chưa làm", "color": "grayLight2"},
                        {"name": "Đang làm", "color": "yellowLight2"},
                        {"name": "Hoàn thành", "color": "greenLight2"},
                        {"name": "Hủy", "color": "redLight2"},
                        {"name": "Dời lịch", "color": "orangeLight2"},
                    ]
                },
            },
            {"name": "Ghi chú", "type": "multilineText"},
        ],
    }


def cskh_table():
    return {
        "name": "💬 Lịch Sử CSKH",
        "fields": [
            {"name": "Khách hàng", "type": "singleLineText"},
            {
                "name": "Ngày tương tác",
                "type": "date",
                "options": {"dateFormat": {"name": "iso"}},
            },
            {
                "name": "Hình thức",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Gọi điện", "color": "blueLight2"},
                        {"name": "Nhắn tin Zalo", "color": "tealLight2"},
                        {"name": "Nhắn tin Facebook", "color": "blueLight2"},
                        {"name": "Gặp mặt", "color": "greenLight2"},
                        {"name": "Email", "color": "grayLight2"},
                        {"name": "Comment/Inbox", "color": "purpleLight2"},
                    ]
                },
            },
            {"name": "Nội dung", "type": "multilineText"},
            {
                "name": "Kết quả",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Quan tâm cao", "color": "greenLight2"},
                        {"name": "Đang cân nhắc", "color": "yellowLight2"},
                        {"name": "Cần thêm thời gian", "color": "orangeLight2"},
                        {"name": "Từ chối", "color": "redLight2"},
                        {"name": "Chốt được", "color": "greenBright"},
                        {"name": "Không liên lạc được", "color": "grayLight2"},
                    ]
                },
            },
            {"name": "Hành động tiếp theo", "type": "multilineText"},
            {
                "name": "Ngày follow-up",
                "type": "date",
                "options": {"dateFormat": {"name": "iso"}},
            },
            {"name": "Dự án đề cập", "type": "singleLineText"},
        ],
    }


# ─── Create Tables ────────────────────────────────────────────────────────────

def create_table(base_id, schema):
    name = schema["name"]
    r = api("POST", f"{META_URL}/bases/{base_id}/tables", json=schema)
    if ok(r):
        table_id = r.json()["id"]
        print(f"  ✅ Bảng '{name}' (ID: {table_id})")
        return table_id
    else:
        print(f"  ❌ Không tạo được bảng '{name}'")
        return None


# ─── Seed Posts ───────────────────────────────────────────────────────────────

def parse_post(post_dir):
    post_md = post_dir / "post.md"
    if not post_md.exists():
        return None

    content = post_md.read_text(encoding="utf-8")

    # Tiêu đề
    title_match = re.search(r"^#\s+Bài\s+\d+:\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else post_dir.name

    # Số bài
    num_match = re.match(r"^(\d+)-", post_dir.name)
    num = int(num_match.group(1)) if num_match else 0

    # Metadata
    method_match = re.search(r"\*\*Method:\*\*\s*(.+)", content)
    format_match = re.search(r"\*\*Format:\*\*\s*(.+)", content)
    platform_match = re.search(r"\*\*Platform:\*\*\s*(.+)", content)
    status_match = re.search(r"\*\*Status:\*\*\s*(.+)", content)
    date_match = re.search(r"\*\*Date created:\*\*\s*(\d{4}-\d{2}-\d{2})", content)

    # Hook — 2 dòng đầu của Post Text
    hook = ""
    text_match = re.search(r"## Post Text\s*\n+([\s\S]+?)(?:\n---|\n##)", content)
    if text_match:
        lines = [l for l in text_match.group(1).strip().split("\n") if l.strip()]
        hook = "\n".join(lines[:2]) if lines else ""

    # Platform list
    platforms = []
    if platform_match:
        raw = platform_match.group(1)
        if "Facebook" in raw:
            platforms.append("Facebook")
        if "TikTok" in raw:
            platforms.append("TikTok")
        if "Instagram" in raw:
            platforms.append("Instagram")
        if "YouTube" in raw:
            platforms.append("YouTube")

    # Method
    method = ""
    if method_match:
        raw = method_match.group(1).strip()
        if "Viral" in raw:
            method = "Viral Replication"
        elif "Trend" in raw:
            method = "Trend Surfing"
        elif "Pain" in raw:
            method = "Pain Point"

    # Format
    fmt = ""
    if format_match:
        raw = format_match.group(1).strip()
        if "Carousel" in raw or "carousel" in raw:
            fmt = "Carousel"
        elif "Infographic" in raw or "infographic" in raw:
            fmt = "AI Infographic"
        else:
            fmt = "Ảnh cá nhân"

    # Status
    status = "Draft"
    if status_match:
        raw = status_match.group(1).strip().lower()
        if "published" in raw:
            status = "Published"
        elif "approved" in raw:
            status = "Approved"
        elif "scheduled" in raw:
            status = "Scheduled"

    return {
        "Số bài": num,
        "Tiêu đề": title,
        "Hook": hook,
        "Status": status,
        "Platform": platforms,
        "Phương pháp": method if method else None,
        "Format": fmt if fmt else None,
        "Ngày tạo": date_match.group(1) if date_match else None,
        "Slug": post_dir.name,
        "Ghi chú": "",
    }


def seed_posts(base_id, table_id):
    if not POSTS_DIR.exists():
        print("  ⚠️  Thư mục posts/ không tồn tại, bỏ qua seed.")
        return

    post_dirs = sorted([d for d in POSTS_DIR.iterdir() if d.is_dir() and d.name != "README.md"])
    records = []

    for post_dir in post_dirs:
        data = parse_post(post_dir)
        if data:
            fields = {k: v for k, v in data.items() if v is not None and v != [] and v != ""}
            records.append({"fields": fields})

    # Airtable giới hạn 10 records/request
    batches = [records[i : i + 10] for i in range(0, len(records), 10)]
    imported = 0

    for batch in batches:
        r = api("POST", f"{RECORDS_URL}/{base_id}/{table_id}", json={"records": batch})
        if ok(r):
            imported += len(batch)
        time.sleep(0.3)  # rate limit

    print(f"  ✅ Đã import {imported}/{len(records)} posts")


def seed_projects(base_id, table_id):
    projects = [
        {
            "Tên dự án": "Sun Symphony Residence 5",
            "Chủ đầu tư": "Sun Group",
            "Vị trí": "Đà Nẵng",
            "Trạng thái": "Đang mở bán",
            "Slug context": "sun-symphony-residence5",
        },
        {
            "Tên dự án": "Vinhomes Hải Vân Bay",
            "Chủ đầu tư": "Vinhomes",
            "Vị trí": "Liên Chiểu, Đà Nẵng",
            "Trạng thái": "Sắp mở bán",
            "Slug context": "vinhomes-hai-van-bay",
        },
        {
            "Tên dự án": "FourS Tower",
            "Chủ đầu tư": "FourS",
            "Vị trí": "Đà Nẵng",
            "Trạng thái": "Đang mở bán",
            "Slug context": "fours-tower",
        },
    ]

    records = [{"fields": p} for p in projects]
    r = api("POST", f"{RECORDS_URL}/{base_id}/{table_id}", json={"records": records})
    if ok(r):
        print(f"  ✅ Đã seed {len(projects)} dự án")


# ─── Delete temp table ────────────────────────────────────────────────────────

def delete_table(base_id, table_id):
    r = api("DELETE", f"{META_URL}/bases/{base_id}/tables/{table_id}")
    if ok(r):
        print(f"  🗑️  Đã xóa bảng tạm")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n🚀 Airtable Workspace Setup — Bình Phan BĐS")
    print("=" * 50)

    # 1. Tạo hoặc chọn base
    print("\n📦 Bước 1: Tạo base...")
    base_id = create_base()

    if not base_id:
        print("\n⚠️  Không tạo được base tự động.")
        print("   Hãy tạo base thủ công tại airtable.com rồi nhập Base ID:")
        base_id = input("   Base ID (appXXXXXXXX): ").strip()
        if not base_id.startswith("app"):
            print("❌ Base ID không hợp lệ")
            sys.exit(1)

    # Lưu base_id vào .env
    env_path = Path(__file__).parent.parent / ".env"
    env_content = env_path.read_text()
    if "AIRTABLE_BASE_ID" not in env_content:
        env_path.write_text(env_content + f"\nAIRTABLE_BASE_ID={base_id}\n")
        print(f"  💾 Đã lưu AIRTABLE_BASE_ID={base_id} vào .env")

    # Xóa bảng tạm nếu có
    r = api("GET", f"{META_URL}/bases/{base_id}/tables")
    if ok(r):
        tables = r.json().get("tables", [])
        temp = next((t for t in tables if t["name"] == "_setup_temp"), None)
        if temp:
            delete_table(base_id, temp["id"])

    # 2. Tạo các bảng
    print("\n📋 Bước 2: Tạo bảng...")
    table_ids = {}

    for schema in [posts_table(), customers_table(), projects_table(), schedule_table(), cskh_table()]:
        tid = create_table(base_id, schema)
        if tid:
            table_ids[schema["name"]] = tid
        time.sleep(0.5)

    # 3. Seed dữ liệu
    print("\n🌱 Bước 3: Seed dữ liệu...")

    posts_tid = table_ids.get("📝 Posts")
    if posts_tid:
        seed_posts(base_id, posts_tid)

    projects_tid = table_ids.get("🏗️ Dự Án")
    if projects_tid:
        seed_projects(base_id, projects_tid)

    # 4. Kết quả
    print("\n" + "=" * 50)
    print("✅ HOÀN THÀNH!")
    print(f"\n🔗 Mở Airtable base:")
    print(f"   https://airtable.com/{base_id}")
    print(f"\n📌 Base ID đã lưu vào .env: AIRTABLE_BASE_ID={base_id}")
    print("\nCác bảng đã tạo:")
    for name in table_ids:
        print(f"  • {name}")


if __name__ == "__main__":
    main()
