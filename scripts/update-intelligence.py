#!/usr/bin/env python3
"""
Cập nhật intelligence files từ Apify TikTok scraper.
Ngân sách: ~$1.65/lần — 2 lần/tháng trong $5 free tier Apify.

Usage:
    python3 scripts/update-intelligence.py
    python3 scripts/update-intelligence.py --dry-run
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import requests

WORKSPACE = Path(__file__).parent.parent

# Hashtag TikTok BĐS Việt Nam — chỉnh sửa tại đây nếu muốn
TIKTOK_HASHTAGS = [
    "bdsdanang",
    "batdongsan",
    "nhadautu",
    "bdsvietnam",
    "canhodanang",
    "dautubatnongsan",
    "bdsdalat",
    "nhabds",
]

# Facebook post URLs để scrape comments (thêm thủ công, 1 URL mỗi dòng)
FB_URLS_FILE = WORKSPACE / "context" / "intelligence" / "fb-post-urls.txt"

# Giới hạn ngân sách
TIKTOK_MAX_RESULTS   = 300   # 300 × $0.005 = $1.50
FACEBOOK_MAX_COMMENTS = 100  # per post, tổng ~$0.15


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


def run_actor(api_key: str, actor_id: str, input_data: dict, timeout: int = 300) -> list:
    url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items"
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        json=input_data,
        params={"timeout": timeout},
        timeout=timeout + 30,
    )
    r.raise_for_status()
    result = r.json()
    return result if isinstance(result, list) else []


def scrape_tiktok(api_key: str, dry_run: bool) -> list:
    print(f"🎵 TikTok scraper — {TIKTOK_MAX_RESULTS} posts từ #{', #'.join(TIKTOK_HASHTAGS)}")
    if dry_run:
        print("   [DRY RUN] bỏ qua API call")
        return []

    items = run_actor(api_key, "clockworks~tiktok-scraper", {
        "hashtags":              TIKTOK_HASHTAGS,
        "resultsPerPage":        30,
        "maxResults":            TIKTOK_MAX_RESULTS,
        "shouldDownloadVideos":  False,
        "shouldDownloadCovers":  False,
        "shouldDownloadSubtitles": False,
    })
    print(f"   ✅ {len(items)} posts")
    return items


def scrape_facebook_comments(api_key: str, dry_run: bool) -> list:
    if not FB_URLS_FILE.exists():
        print("💬 Facebook Comments — bỏ qua (fb-post-urls.txt chưa có)")
        print(f"   Thêm URL vào: {FB_URLS_FILE.relative_to(WORKSPACE)}")
        return []

    urls = [u.strip() for u in FB_URLS_FILE.read_text().splitlines()
            if u.strip() and not u.startswith("#")]
    if not urls:
        print("💬 Facebook Comments — bỏ qua (fb-post-urls.txt trống)")
        return []

    print(f"💬 Facebook Comments — {len(urls)} posts × {FACEBOOK_MAX_COMMENTS} comments")
    if dry_run:
        print("   [DRY RUN] bỏ qua API call")
        return []

    items = run_actor(api_key, "apify~facebook-comments-scraper", {
        "startUrls":           [{"url": u} for u in urls],
        "maxComments":         FACEBOOK_MAX_COMMENTS,
        "includeNestedComments": False,
    })
    print(f"   ✅ {len(items)} comments")
    return items


def save_raw(data: dict, label: str):
    out_dir = WORKSPACE / "outputs" / "intelligence-raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = out_dir / f"{date_str}-{label}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"   💾 {path.relative_to(WORKSPACE)}")


def print_tiktok_summary(items: list):
    if not items:
        print("   (không có dữ liệu)")
        return

    sorted_items = sorted(items, key=lambda x: x.get("playCount", 0), reverse=True)
    print(f"\n{'='*65}")
    print(f"📊 TIKTOK SUMMARY — Top 20 / {len(items)} posts (Claude phân tích)")
    print(f"{'='*65}")
    for i, it in enumerate(sorted_items[:20], 1):
        views  = it.get("playCount", 0)
        likes  = it.get("diggCount", 0)
        desc   = (it.get("text") or it.get("desc") or "")[:80]
        author = (it.get("authorMeta") or {}).get("name", "") or \
                 (it.get("author") or {}).get("uniqueId", "?")
        print(f"{i:>2}. @{author} | {views:>10,} views | {likes:>8,} likes | {desc}")


def print_comment_summary(items: list):
    if not items:
        return
    print(f"\n{'='*65}")
    print(f"💬 FACEBOOK COMMENTS SUMMARY — {len(items)} comments (Claude phân tích)")
    print(f"{'='*65}")
    for it in items[:60]:
        text = (it.get("text") or "")[:120].strip()
        if text:
            print(f"- {text}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="In config, không gọi Apify API")
    args = parser.parse_args()

    env = load_env()
    api_key = env.get("APIFY_API_KEY", "")
    if not api_key and not args.dry_run:
        print("❌ Thiếu APIFY_API_KEY trong .env")
        return

    print("🚀 update-intelligence — bắt đầu scrape")
    print(f"   Ngân sách ước tính: ~$1.65 (TikTok {TIKTOK_MAX_RESULTS} items)")
    print()

    tiktok_items  = scrape_tiktok(api_key, args.dry_run)
    comment_items = scrape_facebook_comments(api_key, args.dry_run)

    if tiktok_items:
        save_raw({"items": tiktok_items}, "tiktok")
    if comment_items:
        save_raw({"items": comment_items}, "facebook-comments")

    print_tiktok_summary(tiktok_items)
    print_comment_summary(comment_items)

    print(f"\n{'='*65}")
    print("✅ Scrape xong. Claude đọc summary trên và:")
    print("   1. Overwrite context/intelligence/viral-patterns.md")
    print("   2. Overwrite nội dung context/intelligence/audience-painpoints.md")
    print("   3. Cập nhật timestamp ở đầu mỗi file")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
