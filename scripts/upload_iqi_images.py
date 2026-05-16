#!/usr/bin/env python3
"""
Upload ảnh IQI Posts lên Cloudinary → điền Slide URLs vào Airtable.

Quy trình:
  1. Đọc records IQI Posts có "Ảnh Đính Kèm" nhưng chưa có "Slide URLs"
  2. Download từng ảnh đính kèm (Airtable signed URL)
  3. Upload lên Cloudinary: binh-phan-bds/iqi-posts/{record_id}/slide-00, 01...
  4. Ghi JSON array URLs vào field "Slide URLs"

Usage:
    python3 scripts/upload_iqi_images.py            # tất cả record thiếu Slide URLs
    python3 scripts/upload_iqi_images.py --force    # re-upload kể cả đã có
    python3 scripts/upload_iqi_images.py --rec recXXXXXXXXXXXXXX  # 1 record cụ thể
"""

import argparse
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

import requests

WORKSPACE = Path(__file__).parent.parent

IQI_TABLE = "tblhLcemzxd9H0aHF"


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


# ── Cloudinary ────────────────────────────────────────────────────────────────

def cld_sign(params: dict, secret: str) -> str:
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hashlib.sha1(f"{query}{secret}".encode()).hexdigest()


def upload_to_cloudinary(img_bytes: bytes, filename: str, public_id: str,
                         cloud: str, key: str, secret: str) -> str:
    ts     = int(time.time())
    params = {"public_id": public_id, "timestamp": ts}
    sig    = cld_sign(params, secret)
    suffix = Path(filename).suffix.lower()
    mime   = {"png": "image/png", "jpg": "image/jpeg",
              "jpeg": "image/jpeg", "webp": "image/webp"}.get(suffix.lstrip("."), "image/jpeg")

    resp = requests.post(
        f"https://api.cloudinary.com/v1_1/{cloud}/image/upload",
        data={**params, "api_key": key, "signature": sig},
        files={"file": (filename, img_bytes, mime)},
        timeout=60,
    )
    if resp.status_code in (200, 201):
        return resp.json()["secure_url"]
    raise RuntimeError(f"Cloudinary upload thất bại ({resp.status_code}): {resp.text[:300]}")


# ── Airtable ──────────────────────────────────────────────────────────────────

def fetch_records(at_key: str, at_base: str, target_rec: str = None) -> list:
    headers = {"Authorization": f"Bearer {at_key}"}
    params  = {
        "fields[]": ["Tiêu Đề / Hook", "Ảnh Đính Kèm", "Slide URLs"],
        "pageSize": 100,
    }
    if target_rec:
        params["filterByFormula"] = f"RECORD_ID()='{target_rec}'"

    records = []
    offset  = None
    while True:
        if offset:
            params["offset"] = offset
        r = requests.get(
            f"https://api.airtable.com/v0/{at_base}/{IQI_TABLE}",
            headers=headers, params=params,
        )
        r.raise_for_status()
        data = r.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records


def update_slide_urls(at_key: str, at_base: str, rec_id: str, urls: list):
    requests.patch(
        f"https://api.airtable.com/v0/{at_base}/{IQI_TABLE}/{rec_id}",
        headers={"Authorization": f"Bearer {at_key}", "Content-Type": "application/json"},
        json={"fields": {"Slide URLs": json.dumps(urls)}},
    ).raise_for_status()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force",  action="store_true", help="Re-upload kể cả đã có Slide URLs")
    parser.add_argument("--rec",    help="Chỉ xử lý 1 record ID cụ thể")
    args = parser.parse_args()

    env    = load_env()
    at_key = env.get("AIRTABLE_API_KEY", "")
    at_base = env.get("AIRTABLE_BASE_ID", "")
    cld_cloud  = env.get("CLOUDINARY_CLOUD_NAME", "")
    cld_key    = env.get("CLOUDINARY_API_KEY", "")
    cld_secret = env.get("CLOUDINARY_API_SECRET", "")

    if not all([at_key, at_base]):
        print("❌ Thiếu AIRTABLE_API_KEY / AIRTABLE_BASE_ID")
        return
    if not all([cld_cloud, cld_key, cld_secret]):
        print("❌ Thiếu CLOUDINARY_CLOUD_NAME / CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET")
        return

    print("☁️  IQI Images → Cloudinary → Airtable Slide URLs\n")

    records = fetch_records(at_key, at_base, target_rec=args.rec)
    print(f"Tổng records lấy được: {len(records)}")

    uploaded = skipped = no_image = errors = 0

    for rec in records:
        rec_id     = rec["id"]
        fields     = rec.get("fields", {})
        title      = fields.get("Tiêu Đề / Hook", rec_id)[:50]
        attachments = fields.get("Ảnh Đính Kèm", [])
        slide_urls = fields.get("Slide URLs", "")

        if not attachments:
            print(f"  –  {title} — không có ảnh đính kèm")
            no_image += 1
            continue

        if slide_urls and not args.force:
            print(f"  ✓  {title} — đã có Slide URLs, bỏ qua")
            skipped += 1
            continue

        print(f"  ↑  {title} ({len(attachments)} ảnh) ...", end=" ", flush=True)
        try:
            urls = []
            for i, att in enumerate(attachments):
                att_url  = att.get("url", "")
                filename = att.get("filename", f"image-{i:02d}.jpg")
                if not att_url:
                    continue

                # Download từ Airtable
                img_resp = requests.get(att_url, timeout=30)
                img_resp.raise_for_status()
                img_bytes = img_resp.content

                # Upload lên Cloudinary
                public_id = f"binh-phan-bds/iqi-posts/{rec_id}/slide-{i:02d}"
                url = upload_to_cloudinary(
                    img_bytes, filename, public_id,
                    cld_cloud, cld_key, cld_secret,
                )
                urls.append(url)

                if i < len(attachments) - 1:
                    time.sleep(0.3)

            if urls:
                update_slide_urls(at_key, at_base, rec_id, urls)
                print(f"✅  ({len(urls)} URLs)")
                uploaded += 1
            else:
                print("⚠️  không lấy được URL nào")
                errors += 1

        except Exception as e:
            print(f"❌  {e}")
            errors += 1

        time.sleep(0.5)

    print(f"\nHoàn thành: {uploaded} upload, {skipped} bỏ qua, {no_image} không có ảnh, {errors} lỗi")


if __name__ == "__main__":
    main()
