#!/usr/bin/env python3
"""
Cập nhật intelligence files từ Apify TikTok.
- Scrape posts theo hashtag → viral-patterns.md
- Scrape comments từ top posts → audience-painpoints.md
Ngân sách: ~$2.00/lần — 2 lần/tháng trong $5 free tier Apify.

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

# Hashtag TikTok BĐS Việt Nam
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

# Giới hạn ngân sách
TIKTOK_MAX_RESULTS    = 300  # 300 × $0.005 = $1.50
TOP_POSTS_FOR_COMMENTS = 5   # top 5 bài views cao nhất
COMMENTS_PER_POST     = 20   # 5 × 20 × $0.005 = $0.50
# Tổng ước tính: ~$2.00/lần


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


def scrape_tiktok_posts(api_key: str, dry_run: bool) -> list:
    print(f"🎵 TikTok Posts — {TIKTOK_MAX_RESULTS} posts từ #{', #'.join(TIKTOK_HASHTAGS)}")
    if dry_run:
        print("   [DRY RUN] bỏ qua")
        return []

    items = run_actor(api_key, "clockworks~tiktok-scraper", {
        "hashtags":                TIKTOK_HASHTAGS,
        "resultsPerPage":          30,
        "maxResults":              TIKTOK_MAX_RESULTS,
        "shouldDownloadVideos":    False,
        "shouldDownloadCovers":    False,
        "shouldDownloadSubtitles": False,
    })
    print(f"   ✅ {len(items)} posts")
    return items


def pick_top_posts(posts: list, n: int) -> list:
    """Chọn top N bài theo comment count, chỉ xét bài views ≥ 10,000."""
    qualified = [p for p in posts if p.get("playCount", 0) >= 10_000]
    ranked = sorted(qualified, key=lambda x: x.get("commentCount", 0), reverse=True)

    top = []
    for p in ranked[:n]:
        url = (
            p.get("webVideoUrl")
            or p.get("videoUrl")
            or p.get("url")
        )
        author = (p.get("authorMeta") or {}).get("name", "") or \
                 (p.get("author") or {}).get("uniqueId", "?")
        if url:
            top.append({
                "url":      url,
                "views":    p.get("playCount", 0),
                "comments": p.get("commentCount", 0),
                "author":   author,
                "desc":     (p.get("text") or p.get("desc") or "")[:80],
            })

    print(f"\n   🔍 {len(qualified)}/{len(posts)} bài đạt ngưỡng ≥ 10K views")
    print(f"   🏆 Top {len(top)} bài nhiều comment nhất → scrape comments:")
    for i, p in enumerate(top, 1):
        print(f"      {i}. @{p['author']} | {p['views']:,} views | {p['comments']:,} comments | {p['desc']}")
    return top


def is_useful_comment(text: str) -> bool:
    """Lọc comment không có giá trị: emoji-only, quá ngắn, @mention."""
    if not text or len(text.strip()) < 10:
        return False
    if text.strip().startswith("@"):
        return False
    # Bỏ comment toàn emoji / ký tự đặc biệt không có chữ cái
    has_letter = any(c.isalpha() for c in text)
    return has_letter


def scrape_tiktok_comments(api_key: str, top_posts: list, dry_run: bool) -> list:
    if not top_posts:
        print("💬 TikTok Comments — bỏ qua (không có post URL)")
        return []

    print(f"\n💬 TikTok Comments — {len(top_posts)} posts × top {COMMENTS_PER_POST} (sort by likes)")
    if dry_run:
        print("   [DRY RUN] bỏ qua")
        return []

    all_comments = []
    for p in top_posts:
        try:
            items = run_actor(api_key, "clockworks~tiktok-scraper", {
                "postURLs":        [p["url"]],
                "maxComments":     COMMENTS_PER_POST * 3,  # lấy nhiều hơn để có dư sau lọc
                "scrapeType":      "comments",
                "commentSortType": "top",                  # sort by likes
            }, timeout=120)

            # Sort by likes, lọc comment vô nghĩa, giữ top N
            useful = [c for c in items if is_useful_comment(
                c.get("text") or c.get("comment") or ""
            )]
            useful.sort(key=lambda c: c.get("likeCount", 0), reverse=True)
            top_comments = useful[:COMMENTS_PER_POST]

            all_comments.extend(top_comments)
            print(f"   ✅ @{p['author']}: {len(top_comments)}/{len(items)} comments hữu ích")
        except Exception as e:
            print(f"   ⚠️  @{p['author']}: lỗi — {e}")

    print(f"   📦 Tổng: {len(all_comments)} comments sạch")
    return all_comments


def save_raw(data: dict, label: str):
    out_dir = WORKSPACE / "outputs" / "intelligence-raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = out_dir / f"{date_str}-{label}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"   💾 {path.relative_to(WORKSPACE)}")


def print_posts_summary(posts: list):
    if not posts:
        return
    ranked = sorted(posts, key=lambda x: x.get("playCount", 0), reverse=True)
    print(f"\n{'='*65}")
    print(f"📊 TIKTOK POSTS — Top 20 / {len(posts)} (Claude phân tích viral patterns)")
    print(f"{'='*65}")
    for i, it in enumerate(ranked[:20], 1):
        views  = it.get("playCount", 0)
        likes  = it.get("diggCount", 0)
        desc   = (it.get("text") or it.get("desc") or "")[:75]
        author = (it.get("authorMeta") or {}).get("name", "") or \
                 (it.get("author") or {}).get("uniqueId", "?")
        print(f"{i:>2}. @{author} | {views:>10,} views | {likes:>7,} likes | {desc}")


def print_comments_summary(comments: list):
    if not comments:
        return
    print(f"\n{'='*65}")
    print(f"💬 TIKTOK COMMENTS — {len(comments)} comments sạch (Claude phân tích pain points)")
    print(f"{'='*65}")
    for c in comments:
        text  = (c.get("text") or c.get("comment") or "")[:120].strip()
        likes = c.get("likeCount", 0)
        if text:
            print(f"[{likes:>4} likes] {text}")


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

    print("🚀 update-intelligence — bắt đầu")
    print(f"   Posts: {TIKTOK_MAX_RESULTS} (~$1.50) | Comments: {TOP_POSTS_FOR_COMMENTS}×{COMMENTS_PER_POST} (~$0.50) | Tổng: ~$2.00")
    print()

    # Bước 1: Scrape posts theo hashtag
    posts = scrape_tiktok_posts(api_key, args.dry_run)
    if posts:
        save_raw({"items": posts}, "tiktok-posts")

    # Bước 2: Chọn top posts → scrape comments
    top_posts = pick_top_posts(posts, TOP_POSTS_FOR_COMMENTS) if posts else []
    comments  = scrape_tiktok_comments(api_key, top_posts, args.dry_run)
    if comments:
        save_raw({"items": comments}, "tiktok-comments")

    # Summary cho Claude phân tích
    print_posts_summary(posts)
    print_comments_summary(comments)

    print(f"\n{'='*65}")
    print("✅ Scrape xong. Claude đọc summary trên và:")
    print("   1. OVERWRITE context/intelligence/viral-patterns.md")
    print("      → nhóm theo hook-type, giữ top 12–15 patterns")
    print("   2. OVERWRITE nội dung context/intelligence/audience-painpoints.md")
    print("      → phân vào 6 nhóm chủ đề cố định, paraphrase không copy")
    print("   3. Cập nhật timestamp ở đầu mỗi file")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
