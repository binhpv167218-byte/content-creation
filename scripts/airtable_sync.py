#!/usr/bin/env python3
"""
Airtable Sync — Posts
Upsert tất cả posts trong posts/ lên bảng '📝 Posts' của Airtable.
Chạy độc lập hoặc được gọi từ build-dashboard.py.

Usage:
    python3 scripts/airtable_sync.py            # sync tất cả
    python3 scripts/airtable_sync.py --post 025-slug  # sync 1 post cụ thể
"""

import random
import re
import sys
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
POSTS_DIR = WORKSPACE / "posts"


def load_env():
    env = {}
    env_file = WORKSPACE / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


ENV = load_env()
API_KEY  = ENV.get("AIRTABLE_API_KEY", "")
BASE_ID  = ENV.get("AIRTABLE_BASE_ID", "")
TABLE_ID = "📝 Posts"

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{requests.utils.quote(TABLE_ID)}"


# ─── Parse post.md ─────────────────────────────────────────────────────────────

def parse_post(post_dir: Path):
    md = post_dir / "post.md"
    if not md.exists():
        return None

    content = md.read_text(encoding="utf-8")

    title_m    = re.search(r"^#\s+Bài\s+\d+:\s+(.+)$", content, re.MULTILINE)
    num_m      = re.match(r"^(\d+)-", post_dir.name)
    method_m   = re.search(r"\*\*Method:\*\*\s*(.+)", content)
    format_m   = re.search(r"\*\*Format:\*\*\s*(.+)", content)
    plat_m     = re.search(r"\*\*Platform:\*\*\s*(.+)", content)
    date_m     = re.search(r"\*\*Date created:\*\*\s*(\d{4}-\d{2}-\d{2})", content)
    pub_m      = re.search(r"\*\*Ngày đăng:\*\*\s*(\d{2}/\d{2}/\d{4})", content)
    lich_m     = re.search(r"\*\*Lịch đăng:\*\*\s*(.+)", content)
    dang_luc_m = re.search(r"\*\*Đăng lúc:\*\*\s*(.+)", content)
    status_m   = re.search(r"\*\*Status:\*\*\s*(.+)", content)
    proj_m     = re.search(r"\*\*Dự án.*?:\*\*\s*(.+)", content)

    # Hook + Nội dung — lấy từ Post Text
    hook = ""
    noidung = ""
    text_m = re.search(r"## Post Text\s*\n+([\s\S]+?)(?:\n---|\n##)", content)
    if text_m:
        full_text = text_m.group(1).strip()
        lines = [l for l in full_text.split("\n") if l.strip()]
        hook = "\n".join(lines[:2])
        noidung = full_text

    # Platform list — hỗ trợ "Facebook IQI", "Facebook BMN" và legacy "Facebook"
    platforms = []
    if plat_m:
        raw = plat_m.group(1)
        if "Facebook IQI" in raw:
            platforms.append("Facebook IQI")
        if "Facebook BMN" in raw:
            platforms.append("Facebook BMN")
        # Legacy: "Facebook" không kèm IQI/BMN → backward compat
        if "Facebook" in raw and "Facebook IQI" not in raw and "Facebook BMN" not in raw:
            platforms.append("Facebook")
        for p in ["TikTok", "Instagram", "Threads", "YouTube"]:
            if p in raw:
                platforms.append(p)

    # Method
    method = ""
    if method_m:
        raw = method_m.group(1)
        if "Viral" in raw:   method = "Viral Replication"
        elif "Trend" in raw: method = "Trend Surfing"
        elif "Pain" in raw:  method = "Pain Point"

    # Format
    fmt = ""
    if format_m:
        raw = format_m.group(1)
        if "Carousel" in raw or "carousel" in raw: fmt = "Carousel"
        elif "Infographic" in raw:                 fmt = "AI Infographic"
        else:                                      fmt = "Ảnh cá nhân"

    # Status
    status = "Draft"
    if status_m:
        raw = status_m.group(1).lower()
        if "published" in raw:   status = "Published"
        elif "approved" in raw:  status = "Approved"
        elif "scheduled" in raw: status = "Scheduled"
        elif "chờ duyệt" in raw: status = "Chờ duyệt"

    # Ngày đăng — parse từ **Ngày đăng:** DD/MM/YYYY hoặc **Lịch đăng:** ... DD/MM ...
    pub_date = None
    slot_time = None
    if pub_m:
        d, m, y = pub_m.group(1).split("/")
        pub_date = f"{y}-{m}-{d}"
        slot_m2 = re.search(r"Slot\s+(\d{1,2}:\d{2})", pub_m.string[pub_m.start():pub_m.start()+80])
        if slot_m2:
            slot_time = slot_m2.group(1)
    elif lich_m:
        raw_lich = lich_m.group(1)
        date_in_lich = re.search(r"(\d{2}/\d{2})", raw_lich)
        if date_in_lich:
            d, m = date_in_lich.group(1).split("/")
            pub_date = f"2026-{m}-{d}"
        time_in_lich = re.search(r"(\d{1,2}:\d{2}(?:am|pm)?)", raw_lich)
        if time_in_lich:
            slot_time = time_in_lich.group(1)
        # Platform từ Lịch đăng nếu chưa có
        if not plat_m:
            if "BMN" in raw_lich and "Facebook BMN" not in platforms:
                platforms.append("Facebook BMN")
            if "Kênh cá nhân" in raw_lich or "Kênh CN" in raw_lich:
                if "Facebook" not in platforms and "Facebook BMN" not in platforms:
                    platforms.append("Facebook")
            for p in ["Instagram", "Threads", "TikTok"]:
                if p in raw_lich and p not in platforms:
                    platforms.append(p)

    # Auto-set Scheduled nếu có ngày đăng và chưa Published
    if pub_date and status == "Draft":
        status = "Scheduled"

    # Build full datetime "DD/MM/YYYY HH:MM" với ±180s randomization
    dang_luc_full = None
    raw_slot = dang_luc_m.group(1).strip() if dang_luc_m else slot_time
    if pub_date and raw_slot:
        # Normalize slot: "8:00am"→"08:00", "12:00pm"→"12:00", "12:00"→"12:00"
        t = raw_slot.lower().replace("am", "").replace("pm", "").strip()
        h, mn = t.split(":")
        h = int(h)
        if "pm" in raw_slot.lower() and h != 12:
            h += 12
        elif "am" in raw_slot.lower() and h == 12:
            h = 0
        # ±180s randomization
        jitter = random.randint(-180, 180)
        base = datetime.strptime(pub_date, "%Y-%m-%d") + timedelta(hours=h, minutes=int(mn), seconds=jitter)
        y2, m2, d2 = base.year, base.month, base.day
        dang_luc_full = f"{d2:02d}/{m2:02d}/{y2} {base.hour:02d}:{base.minute:02d}"

    fields: dict = {
        "Slug": post_dir.name,
        "Tiêu đề": title_m.group(1).strip() if title_m else post_dir.name,
        "Status": status,
    }
    if num_m:           fields["Số bài"]      = int(num_m.group(1))
    if hook:            fields["Hook"]         = hook
    if platforms:       fields["Platform"]     = platforms
    if method:          fields["Phương pháp"]  = method
    if fmt:             fields["Format"]       = fmt
    if date_m:          fields["Ngày tạo"]     = date_m.group(1)
    if pub_date:        fields["Ngày đăng"]    = pub_date
    if dang_luc_full:   fields["Đăng lúc"]     = dang_luc_full
    if proj_m:        fields["Dự án liên quan"] = proj_m.group(1).strip()
    if noidung:       fields["Nội dung"]        = noidung

    return fields


# ─── Airtable helpers ──────────────────────────────────────────────────────────

def fetch_all_slugs():
    """Trả về {slug: record_id} cho toàn bộ records hiện có."""
    slug_map = {}
    offset = None
    while True:
        params = {"fields[]": "Slug", "pageSize": 100}
        if offset:
            params["offset"] = offset
        r = requests.get(BASE_URL, headers=HEADERS, params=params)
        if r.status_code != 200:
            print(f"  ⚠️  Không đọc được bảng: {r.text[:200]}")
            break
        data = r.json()
        for rec in data.get("records", []):
            slug = rec.get("fields", {}).get("Slug", "")
            if slug:
                slug_map[slug] = rec["id"]
        offset = data.get("offset")
        if not offset:
            break
    return slug_map


def create_records(batch: list[dict]) -> int:
    r = requests.post(BASE_URL, headers=HEADERS, json={"records": batch, "typecast": True})
    if r.status_code in (200, 201):
        return len(r.json().get("records", []))
    print(f"  ⚠️  Create failed: {r.text[:200]}")
    return 0


def update_records(batch: list[dict]) -> int:
    r = requests.patch(BASE_URL, headers=HEADERS, json={"records": batch, "typecast": True})
    if r.status_code in (200, 201):
        return len(r.json().get("records", []))
    print(f"  ⚠️  Update failed: {r.text[:200]}")
    return 0


# ─── Main sync ─────────────────────────────────────────────────────────────────

def sync(target_slug=None):
    if not API_KEY or not BASE_ID:
        print("  ⚠️  AIRTABLE_API_KEY hoặc AIRTABLE_BASE_ID chưa có trong .env — bỏ qua sync.")
        return

    # Lấy danh sách post dirs
    if target_slug:
        dirs = [POSTS_DIR / target_slug] if (POSTS_DIR / target_slug).exists() else []
    else:
        dirs = sorted([d for d in POSTS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")])

    if not dirs:
        print("  ⚠️  Không tìm thấy post nào.")
        return

    # Parse tất cả
    parsed = [(d, parse_post(d)) for d in dirs]
    parsed = [(d, f) for d, f in parsed if f is not None]

    # Lấy slug map hiện có trên Airtable
    existing = fetch_all_slugs()

    to_create = []
    to_update = []

    for _, fields in parsed:
        slug = fields["Slug"]
        if slug in existing:
            to_update.append({"id": existing[slug], "fields": fields})
        else:
            to_create.append({"fields": fields})

    created = updated = 0

    # Create theo batch 10
    for i in range(0, len(to_create), 10):
        created += create_records(to_create[i:i+10])
        time.sleep(0.25)

    # Update theo batch 10
    for i in range(0, len(to_update), 10):
        updated += update_records(to_update[i:i+10])
        time.sleep(0.25)

    total = created + updated
    parts = []
    if created: parts.append(f"{created} mới")
    if updated: parts.append(f"{updated} cập nhật")
    label = ", ".join(parts) if parts else "không có thay đổi"
    print(f"  Airtable sync: {label} ({total}/{len(parsed)} posts)")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    target = None
    if "--post" in sys.argv:
        idx = sys.argv.index("--post")
        if idx + 1 < len(sys.argv):
            target = sys.argv[idx + 1]

    print("🔄 Airtable sync...")
    sync(target)
