#!/usr/bin/env python3
"""
Upload video render lên Cloudinary + tạo Airtable record sẵn sàng đăng.

Usage:
    python3 scripts/upload_video.py video-metro-danang \
        --date 11/06/2026 --time 08:00 \
        --platform "BMN, TikTok" \
        --caption "Caption text"

    python3 scripts/upload_video.py video-metro-danang --dry-run
"""

import argparse
import hashlib
import json
import time
import requests
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
STUDIO    = WORKSPACE / "studio"
AT_TABLE  = "tbll5ikhBQPeak8xR"


def load_env():
    env = {}
    for line in (WORKSPACE / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


ENV = load_env()

CLD_CLOUD  = ENV.get("CLOUDINARY_CLOUD_NAME", "")
CLD_KEY    = ENV.get("CLOUDINARY_API_KEY", "")
CLD_SECRET = ENV.get("CLOUDINARY_API_SECRET", "")

AT_KEY = ENV.get("AIRTABLE_API_KEY", "")
AT_BASE = ENV.get("AIRTABLE_BASE_ID", "")
AT_URL  = f"https://api.airtable.com/v0/{AT_BASE}/{AT_TABLE}"
AT_HDR  = {"Authorization": f"Bearer {AT_KEY}", "Content-Type": "application/json"}


def cld_sign(params: dict) -> str:
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hashlib.sha1(f"{query}{CLD_SECRET}".encode()).hexdigest()


def upload_cloudinary(file_path: Path, public_id: str, resource_type: str = "image") -> str:
    ts     = int(time.time())
    params = {"public_id": public_id, "timestamp": ts}
    sig    = cld_sign(params)
    url    = f"https://api.cloudinary.com/v1_1/{CLD_CLOUD}/{resource_type}/upload"
    with open(file_path, "rb") as f:
        r = requests.post(
            url,
            data={**params, "api_key": CLD_KEY, "signature": sig},
            files={"file": (file_path.name, f)},
            timeout=300,
        )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Cloudinary lỗi ({r.status_code}): {r.text[:300]}")
    return r.json()["secure_url"]


def create_airtable_record(fields: dict) -> str:
    r = requests.post(AT_URL, headers=AT_HDR, json={"records": [{"fields": fields}], "typecast": True})
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Airtable lỗi ({r.status_code}): {r.text[:300]}")
    return r.json()["records"][0]["id"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project",   help="Tên project trong studio/ (vd: video-metro-danang)")
    parser.add_argument("--date",     required=True, help="Ngày đăng DD/MM/YYYY")
    parser.add_argument("--time",     required=True, help="Giờ đăng HH:MM")
    parser.add_argument("--platform", required=True, help="Nền tảng (vd: 'BMN, TikTok')")
    parser.add_argument("--caption",  required=True, help="Nội dung caption")
    parser.add_argument("--dry-run",  action="store_true")
    args = parser.parse_args()

    project_dir = STUDIO / args.project
    if not project_dir.exists():
        print(f"Không tìm thấy project: {project_dir}")
        return

    renders_dir = project_dir / "renders"
    mp4s   = sorted(renders_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    thumbs = list(renders_dir.glob("thumbnail.jpg"))

    if not mp4s:
        print(f"Không tìm thấy MP4 trong {renders_dir}")
        return

    mp4_file   = mp4s[0]
    thumb_file = thumbs[0] if thumbs else None

    print(f"Video  : {mp4_file.name}")
    print(f"Thumb  : {thumb_file.name if thumb_file else 'khong co'}")
    print(f"Lich   : {args.date} {args.time} | {args.platform}")
    print(f"Caption: {args.caption[:80]}...")

    if args.dry_run:
        print("DRY RUN -- khong upload that")
        return

    public_id = f"binh-phan-bds/videos/{args.project}"

    print("\nUpload video len Cloudinary...")
    video_url = upload_cloudinary(mp4_file, public_id, resource_type="video")
    print(f"  OK: {video_url}")

    thumb_url = None
    if thumb_file:
        print("Upload thumbnail...")
        thumb_url = upload_cloudinary(thumb_file, f"{public_id}-thumb", resource_type="image")
        print(f"  OK: {thumb_url}")

    d, m, y   = args.date.split("/")
    ngay_dang = f"{y}-{m}-{d}"
    dang_luc  = f"{args.date} {args.time}"
    platforms = [p.strip() for p in args.platform.split(",")]

    fields = {
        "Slug":        args.project,
        "Format":      "Video Market",
        "Platform":    platforms,
        "Nội dung":    args.caption,
        "Ngày đăng":   ngay_dang,
        "Đăng lúc":    dang_luc,
        "Slide URLs":  json.dumps([video_url]),
        "Status":      "Scheduled",
    }
    if thumb_url:
        fields["Ảnh URL"] = thumb_url

    print("\nTao Airtable record...")
    rec_id = create_airtable_record(fields)
    print(f"  OK: {rec_id}")
    print(f"\nSan sang dang luc {dang_luc}!")


if __name__ == "__main__":
    main()
