#!/usr/bin/env python3
"""
Cập nhật intelligence files từ Apify TikTok.
- Scrape posts theo hashtag BĐS Đà Nẵng → viral-patterns.md
- Scrape comments thật từ top posts → audience-painpoints.md
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

# Hashtag TẬP TRUNG vào Đà Nẵng — bỏ hashtag chung chung
TIKTOK_HASHTAGS = [
    # Bất động sản Đà Nẵng
    "bdsdanang",
    "batdongsandanang",
    "canhodanang",
    "dautudanang",
    # Cho thuê tại Đà Nẵng
    "chothuecanhodanang",
    "chothuedanang",
    "appartmentdanang",
    # Chuyển đến / sống tại Đà Nẵng
    "chuyendensongdanang",
    "songodanang",
    "cuocsongdanang",
    "thanhphodangsong",
    "bophovebien",
]

# Giới hạn ngân sách
TIKTOK_MAX_RESULTS     = 300   # 300 × $0.005 = $1.50
MAX_POSTS_PER_ACCOUNT  = 2     # tránh 1 account chiếm hết top
MIN_VIEWS              = 10_000
TOP_POSTS_FOR_COMMENTS = 5
COMMENTS_PER_POST      = 20    # 5 × 20 × $0.005 = $0.50
COMMENTS_FETCH_BUFFER  = 60    # lấy nhiều hơn để có dư sau lọc
# Tổng ước tính: ~$2.00/lần

# Keyword Đà Nẵng — lọc chặt hơn, đúng chủ đề hơn
DANANG_KEYWORDS = [
    "đà nẵng", "da nang", "danang",
    "căn hộ", "chung cư", "dự án",
    "cho thuê", "chuyển đến", "sống tại", "định cư",
    "mua nhà", "đầu tư", "bất động sản",
    "biển", "ven biển", "view biển",
]


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


def is_danang_post(post: dict) -> bool:
    """Chỉ giữ bài có liên quan Đà Nẵng hoặc BĐS cụ thể."""
    caption = (post.get("text") or post.get("desc") or "").lower()
    return any(kw in caption for kw in DANANG_KEYWORDS)


def pick_top_posts(posts: list, n: int) -> list:
    """
    Chọn top N bài:
    - views >= MIN_VIEWS
    - có keyword Đà Nẵng/BĐS trong caption
    - tối đa MAX_POSTS_PER_ACCOUNT bài/tài khoản
    - sort by comment count
    """
    qualified = [
        p for p in posts
        if p.get("playCount", 0) >= MIN_VIEWS and is_danang_post(p)
    ]

    # Giới hạn số bài per account
    account_count: dict = {}
    diverse = []
    for p in sorted(qualified, key=lambda x: x.get("commentCount", 0), reverse=True):
        author = (p.get("authorMeta") or {}).get("name", "") or \
                 (p.get("author") or {}).get("uniqueId", "?")
        if account_count.get(author, 0) < MAX_POSTS_PER_ACCOUNT:
            diverse.append(p)
            account_count[author] = account_count.get(author, 0) + 1
        if len(diverse) >= n:
            break

    top = []
    for p in diverse:
        url = p.get("webVideoUrl") or p.get("videoUrl") or p.get("url")
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

    total_qualified = len(qualified)
    print(f"\n   🔍 {total_qualified}/{len(posts)} bài đạt ngưỡng (views ≥ {MIN_VIEWS:,} + keyword Đà Nẵng/BĐS)")
    print(f"   🏆 Top {len(top)} bài (max {MAX_POSTS_PER_ACCOUNT}/account) → scrape comments:")
    for i, p in enumerate(top, 1):
        print(f"      {i}. @{p['author']} | {p['views']:,} views | {p['comments']:,} comments | {p['desc']}")
    return top


def is_useful_comment(text: str) -> bool:
    """Lọc comment vô nghĩa: emoji-only, quá ngắn, @mention."""
    if not text or len(text.strip()) < 10:
        return False
    if text.strip().startswith("@"):
        return False
    return any(c.isalpha() for c in text)


def scrape_tiktok_comments(api_key: str, top_posts: list, dry_run: bool) -> list:
    """
    Scrape comment thật bằng cách chạy actor riêng theo từng video URL.
    Dùng clockworks~tiktok-scraper với postURLs — trả về post data kèm comments.
    """
    if not top_posts:
        print("💬 TikTok Comments — bỏ qua (không có post)")
        return []

    print(f"\n💬 TikTok Comments — {len(top_posts)} posts × top {COMMENTS_PER_POST} (sort by likes)")
    if dry_run:
        print("   [DRY RUN] bỏ qua")
        return []

    all_comments = []
    for p in top_posts:
        try:
            # Dùng actor riêng cho từng video, lấy nhiều hơn để lọc
            items = run_actor(api_key, "clockworks~tiktok-scraper", {
                "postURLs":             [p["url"]],
                "shouldScrapeComments": True,
                "maxComments":          COMMENTS_FETCH_BUFFER,
            }, timeout=120)

            # Tìm comments trong response — có thể ở key "comments" hoặc nested
            raw_comments = []
            for item in items:
                if isinstance(item.get("comments"), list):
                    raw_comments.extend(item["comments"])
                elif item.get("type") == "comment" or "likeCount" in item:
                    raw_comments.append(item)

            if not raw_comments:
                print(f"   ⚠️  @{p['author']}: không tìm thấy comments trong response — thử actor khác")
                # Fallback: thử actor tiktok-comment-scraper
                raw_comments = _scrape_comments_fallback(api_key, p["url"])

            useful = [
                c for c in raw_comments
                if is_useful_comment(c.get("text") or c.get("comment") or "")
            ]
            useful.sort(key=lambda c: c.get("likeCount", 0), reverse=True)
            top_comments = useful[:COMMENTS_PER_POST]

            all_comments.extend(top_comments)
            print(f"   ✅ @{p['author']}: {len(top_comments)}/{len(raw_comments)} comments hữu ích")

        except Exception as e:
            print(f"   ❌ @{p['author']}: lỗi — {e}")

    print(f"   📦 Tổng: {len(all_comments)} comments sạch")
    return all_comments


def _scrape_comments_fallback(api_key: str, video_url: str) -> list:
    """Fallback: thử actor apify/tiktok-comment-scraper."""
    try:
        items = run_actor(api_key, "apify~tiktok-comment-scraper", {
            "postURLs": [video_url],
            "maxItems": 60,
        }, timeout=120)
        return items
    except Exception:
        return []


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
        views    = it.get("playCount", 0)
        comments = it.get("commentCount", 0)
        desc     = (it.get("text") or it.get("desc") or "")[:70]
        author   = (it.get("authorMeta") or {}).get("name", "") or \
                   (it.get("author") or {}).get("uniqueId", "?")
        print(f"{i:>2}. @{author} | {views:>9,}v | {comments:>5,}c | {desc}")


def print_comments_summary(comments: list):
    if not comments:
        print("\n⚠️  Không có comment — cần kiểm tra lại actor sau khi chạy thật.")
        return
    print(f"\n{'='*65}")
    print(f"💬 TIKTOK COMMENTS — {len(comments)} comments (Claude phân tích pain points)")
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
    print(f"   Focus: BĐS Đà Nẵng, cho thuê, chuyển đến sống")
    print()

    posts = scrape_tiktok_posts(api_key, args.dry_run)
    if posts:
        save_raw({"items": posts}, "tiktok-posts")

    top_posts = pick_top_posts(posts, TOP_POSTS_FOR_COMMENTS) if posts else []
    comments  = scrape_tiktok_comments(api_key, top_posts, args.dry_run)
    if comments:
        save_raw({"items": comments}, "tiktok-comments")

    print_posts_summary(posts)
    print_comments_summary(comments)

    print(f"\n{'='*65}")
    print("✅ Scrape xong. Claude đọc summary trên và:")
    print("   1. OVERWRITE context/intelligence/viral-patterns.md")
    print("   2. OVERWRITE nội dung context/intelligence/audience-painpoints.md")
    print("   3. Cập nhật timestamp ở đầu mỗi file")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
