#!/usr/bin/env python3
"""
Upload ảnh posts lên Cloudinary → set URL vào Airtable.

- Carousel: upload TẤT CẢ slides, lưu JSON array vào "Slide URLs" (dùng cho TikTok)
- Single image: upload image.png, lưu ["url"] vào Slide URLs
- Tự tạo field "Slide URLs" và "TikTok ID" nếu chưa có

Usage:
    python3 scripts/airtable_upload_images.py           # tất cả
    python3 scripts/airtable_upload_images.py --post 003-sun-symphony-carousel
    python3 scripts/airtable_upload_images.py --force   # re-upload kể cả đã có
"""

import hashlib
import json
import sys
import time
import requests
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
POSTS_DIR = WORKSPACE / "posts"


def load_env():
    env = {}
    for line in (WORKSPACE / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


ENV = load_env()

# Airtable
AT_KEY          = ENV.get("AIRTABLE_API_KEY", "")
AT_BASE         = ENV.get("AIRTABLE_BASE_ID", "")
AT_TABLE        = "tbll5ikhBQPeak8xR"
AT_HEADERS      = {"Authorization": f"Bearer {AT_KEY}", "Content-Type": "application/json"}
AT_REC_URL      = f"https://api.airtable.com/v0/{AT_BASE}/{AT_TABLE}"
META_TABLES_URL = f"https://api.airtable.com/v0/meta/bases/{AT_BASE}/tables"
META_FIELDS_URL = f"https://api.airtable.com/v0/meta/bases/{AT_BASE}/tables/{AT_TABLE}/fields"

# Cloudinary
CLD_CLOUD  = ENV.get("CLOUDINARY_CLOUD_NAME", "")
CLD_KEY    = ENV.get("CLOUDINARY_API_KEY", "")
CLD_SECRET = ENV.get("CLOUDINARY_API_SECRET", "")
CLD_URL    = f"https://api.cloudinary.com/v1_1/{CLD_CLOUD}/image/upload"

# Airtable field names
FIELD_ATT  = "Ảnh"
FIELD_URL  = "Ảnh URL"

# Fields cần đảm bảo tồn tại
REQUIRED_FIELDS = [
    {"name": "Slide URLs", "type": "multilineText"},
    {"name": "TikTok ID",  "type": "singleLineText"},
]


# ── Airtable schema ────────────────────────────────────────────────────────────

def ensure_fields():
    r = requests.get(META_TABLES_URL, headers=AT_HEADERS)
    r.raise_for_status()
    tables = r.json().get("tables", [])
    table = next((t for t in tables if t["id"] == AT_TABLE), None)
    existing = {f["name"] for f in (table.get("fields", []) if table else [])}

    for field in REQUIRED_FIELDS:
        if field["name"] not in existing:
            r = requests.post(META_FIELDS_URL, headers=AT_HEADERS, json=field)
            if r.status_code in (200, 201):
                print(f"  ✅ Tạo field '{field['name']}'")
            else:
                print(f"  ⚠️  Không tạo được '{field['name']}': {r.text[:100]}")
            time.sleep(0.4)


# ── Airtable records ───────────────────────────────────────────────────────────

def fetch_records():
    """Trả về {slug: {id, has_slides}} cho toàn bộ records."""
    result = {}
    offset = None
    while True:
        params = {"fields[]": ["Slug", "Slide URLs"], "pageSize": 100}
        if offset:
            params["offset"] = offset
        r = requests.get(AT_REC_URL, headers=AT_HEADERS, params=params)
        r.raise_for_status()
        data = r.json()
        for rec in data.get("records", []):
            fields = rec.get("fields", {})
            slug = fields.get("Slug", "")
            if slug:
                result[slug] = {
                    "id": rec["id"],
                    "has_slides": bool(fields.get("Slide URLs", "")),
                }
        offset = data.get("offset")
        if not offset:
            break
    return result


def update_airtable_record(record_id, cover_url, all_urls, cover_name):
    r = requests.patch(
        f"{AT_REC_URL}/{record_id}",
        headers=AT_HEADERS,
        json={
            "fields": {
                FIELD_ATT:   [{"url": cover_url, "filename": cover_name}],
                FIELD_URL:   cover_url,
                "Slide URLs": json.dumps(all_urls),
            }
        },
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Airtable update thất bại ({r.status_code}): {r.text[:200]}")


# ── Cloudinary ─────────────────────────────────────────────────────────────────

def cloudinary_sign(params: dict) -> str:
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hashlib.sha1(f"{query}{CLD_SECRET}".encode()).hexdigest()


def upload_to_cloudinary(img_path: Path, public_id: str) -> str:
    ts = int(time.time())
    params = {"public_id": public_id, "timestamp": ts}
    sig = cloudinary_sign(params)
    suffix = img_path.suffix.lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(
        suffix.lstrip("."), "image/png"
    )
    with open(img_path, "rb") as f:
        resp = requests.post(
            CLD_URL,
            data={**params, "api_key": CLD_KEY, "signature": sig},
            files={"file": (img_path.name, f, mime)},
            timeout=60,
        )
    if resp.status_code in (200, 201):
        return resp.json()["secure_url"]
    raise RuntimeError(f"Cloudinary upload thất bại ({resp.status_code}): {resp.text[:200]}")


# ── Files ──────────────────────────────────────────────────────────────────────

def find_all_slides(post_dir: Path):
    """
    Carousel posts: trả về tất cả slide-XX.png theo thứ tự.
    Single image posts: trả về [image.png].
    """
    slides_dir = post_dir / "carousel-slides"
    if slides_dir.exists():
        slides = sorted(slides_dir.glob("slide-*.png"))
        if slides:
            return list(slides)
    for name in ("image.png", "image.jpg", "image.jpeg"):
        p = post_dir / name
        if p.exists():
            return [p]
    return []


def upload_slides(slides, slug):
    """Upload all slide files to Cloudinary. Returns list of URLs."""
    is_carousel = len(slides) > 1
    urls = []
    for i, slide in enumerate(slides):
        public_id = (
            f"binh-phan-bds/{slug}/slide-{i:02d}" if is_carousel
            else f"binh-phan-bds/{slug}"
        )
        # Dùng overwrite=false để skip nếu đã có trên Cloudinary (tiết kiệm API call)
        url = upload_to_cloudinary(slide, public_id)
        urls.append(url)
        if i < len(slides) - 1:
            time.sleep(0.25)
    return urls


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if not all([CLD_CLOUD, CLD_KEY, CLD_SECRET]):
        print("❌ Thiếu CLOUDINARY_CLOUD_NAME / CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET trong .env")
        return

    force = "--force" in sys.argv
    target_slug = None
    if "--post" in sys.argv:
        idx = sys.argv.index("--post")
        if idx + 1 < len(sys.argv):
            target_slug = sys.argv[idx + 1]

    print("☁️  Cloudinary image upload → Airtable...")

    ensure_fields()
    time.sleep(0.5)

    records = fetch_records()
    print(f"  {len(records)} records trong Airtable")

    if target_slug:
        dirs = [POSTS_DIR / target_slug] if (POSTS_DIR / target_slug).exists() else []
    else:
        dirs = sorted([d for d in POSTS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")])

    uploaded = skipped = missing = errors = 0

    for post_dir in dirs:
        slug = post_dir.name
        if slug not in records:
            print(f"  ⚠️  '{slug}' chưa có trong Airtable")
            missing += 1
            continue

        rec = records[slug]
        if rec["has_slides"] and not force:
            print(f"  ✓  {slug} — đã có Slide URLs, bỏ qua")
            skipped += 1
            continue

        slides = find_all_slides(post_dir)
        if not slides:
            print(f"  –  {slug} — không tìm thấy ảnh")
            missing += 1
            continue

        label = f"{len(slides)} slides" if len(slides) > 1 else slides[0].name
        print(f"  ↑  {slug} ← {label} ...", end=" ", flush=True)
        try:
            urls = upload_slides(slides, slug)
            update_airtable_record(rec["id"], urls[0], urls, slides[0].name)
            print(f"✅  ({len(urls)} URLs)")
            uploaded += 1
        except Exception as e:
            print(f"❌  {e}")
            errors += 1

        time.sleep(0.4)

    print(f"\nHoàn thành: {uploaded} upload, {skipped} bỏ qua, {missing} không có ảnh, {errors} lỗi")


if __name__ == "__main__":
    main()
