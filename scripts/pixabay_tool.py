#!/usr/bin/env python3
"""
pixabay_tool.py — Tìm và tải tài nguyên từ Pixabay theo Audio Profile.

Usage:
  python3 scripts/pixabay_tool.py [1|2] [music|sound-effects|image] ["từ khóa bổ sung"]

Ví dụ:
  python3 scripts/pixabay_tool.py 1 music "suspense"
  python3 scripts/pixabay_tool.py 2 sound-effects "click"
  python3 scripts/pixabay_tool.py 1 image "luxury interior"
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PIXABAY_KEY = os.getenv("PIXABAY_API_KEY")

PROFILES = {
    "1": {
        "name": "Quiet Luxury & Cinematic Drama",
        "music_keywords": "cinematic orchestral dark ambient minimalist piano",
        "sfx_keywords": "sub boom cinematic deep rumble clock ticking foley glass",
    },
    "2": {
        "name": "High-Speed Info-Graphic & Finance Podcast",
        "music_keywords": "synthwave tech noir cyberpunk corporate hip hop",
        "sfx_keywords": "digital glitch data counter camera shutter fast whoosh",
    },
}

API_ENDPOINTS = {
    "image": "https://pixabay.com/api/",
    "music": "https://pixabay.com/api/music/",
    "sound-effects": "https://pixabay.com/api/music/",
}


def clean_filename(text):
    return "".join(c for c in text if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")


def search_pixabay(endpoint, query, limit):
    params = {"key": PIXABAY_KEY, "q": query, "per_page": limit}
    resp = requests.get(endpoint, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def search_and_download(profile_id, media_type, custom_query="", limit=3):
    if profile_id not in PROFILES:
        print("Vui lòng chọn Profile '1' hoặc '2'.")
        return

    if media_type not in API_ENDPOINTS:
        print("media_type phải là: music, sound-effects, hoặc image")
        return

    profile = PROFILES[profile_id]
    print(f"Profile {profile_id}: {profile['name']}")

    if media_type == "music":
        base_query = profile["music_keywords"]
    elif media_type == "sound-effects":
        base_query = profile["sfx_keywords"]
    else:
        base_query = "luxury interior architecture" if profile_id == "1" else "finance chart infographic"

    query = f"{base_query} {custom_query}".strip()
    endpoint = API_ENDPOINTS[media_type]

    print(f"Đang tìm: '{query}' tại {endpoint}")

    try:
        data = search_pixabay(endpoint, query, limit)

        if not data.get("hits"):
            print(f"Không có kết quả cho '{query}'. Thử fallback với từ khóa tùy chỉnh...")
            if not custom_query:
                print("Không có từ khóa fallback. Dừng.")
                return
            data = search_pixabay(endpoint, custom_query, limit)
            if not data.get("hits"):
                print("Vẫn không có kết quả.")
                return

        folder = Path(f"outputs/pixabay/Profile_{profile_id}/{media_type}")
        folder.mkdir(parents=True, exist_ok=True)

        for idx, item in enumerate(data["hits"]):
            if media_type in ("music", "sound-effects"):
                # Pixabay music: dùng field 'audio' (preview URL)
                download_url = item.get("audio") or item.get("previews", {}).get("preview-hq-mp3")
                ext = "mp3"
                tags = item.get("tags", f"audio_{idx}").split(",")[0]
                title = clean_filename(tags) or f"audio_{idx}"
            else:
                download_url = item.get("largeImageURL")
                ext = "jpg"
                title = f"image_{item['id']}"

            if not download_url:
                print(f"  Bỏ qua item {idx} — không có URL tải.")
                continue

            file_path = folder / f"{title}.{ext}"
            print(f"  Đang tải: {file_path}")
            file_res = requests.get(download_url, timeout=30)
            file_path.write_bytes(file_res.content)

        print(f"Xong. File lưu tại: {folder}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"403 Forbidden — Pixabay Music API bị Cloudflare chặn với programmatic access.")
            print("Giải pháp: dùng Pixabay qua browser hoặc chuyển sang Freesound (đã cài sẵn).")
        else:
            print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Lỗi: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(0)

    profile_id = sys.argv[1]
    media_type = sys.argv[2]
    custom_query = sys.argv[3] if len(sys.argv) > 3 else ""
    search_and_download(profile_id, media_type, custom_query, limit=3)
