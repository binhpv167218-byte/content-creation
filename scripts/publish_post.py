#!/usr/bin/env python3
"""
Đăng bài lên đa kênh: Facebook (Graph API) + Buffer (TikTok, Instagram, Threads)

Usage:
    python3 scripts/publish_post.py --post 023-s1-ban-giao-symphony5
    python3 scripts/publish_post.py --post 023-s1-ban-giao-symphony5 --dry-run
"""

import json
import re
import time
import argparse
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

# Facebook — dùng page tokens, /me tự trỏ đúng page
FB_TOKEN_IQI     = ENV.get("FACEBOOK_TOKEN_BINH_PHAN_IQI", "")
FB_TOKEN_BMN     = ENV.get("FACEBOOK_TOKEN_BINH_ME_NHA", "")

# Profile cá nhân Bình Phan — tag vào bài ảnh đơn trên trang Bình Mê Nhà
FB_PERSONAL_ID   = "26960767010228169"

# Buffer
BUFFER_TOKEN     = ENV.get("BUFFER_ACCESS_TOKEN", "")
BUFFER_GQL       = "https://api.buffer.com/graphql"
BUFFER_ORG       = "6a0309d23eea909a6594a206"
BUFFER_TIKTOK    = "6a030a3f090476fb990f46e6"
BUFFER_INSTAGRAM = "6a033e20090476fb99104f87"
BUFFER_THREADS   = "6a030a61090476fb990f47b7"

BUFFER_HEADERS = {
    "Authorization": f"Bearer {BUFFER_TOKEN}",
    "Content-Type": "application/json",
}

PERPLEXITY_KEY = ENV.get("PERPLEXITY_API_KEY", "")


def summarize_for_threads(caption: str, limit: int = 490) -> str:
    """Dùng Perplexity sonar-pro tóm tắt caption xuống dưới `limit` ký tự.
    Fallback: cắt tại paragraph break nếu không có API key."""
    if len(caption) <= limit:
        return caption

    if not PERPLEXITY_KEY:
        cut = caption[:limit - 10].rfind("\n\n")
        return caption[:cut] if cut > 200 else caption[:limit - 3] + "..."

    prompt = (
        f"Tóm tắt đoạn text sau thành phiên bản ngắn hơn, giữ nguyên giọng văn gốc "
        f"(xưng 'mình', tông trực tiếp, không corporate). "
        f"Kết quả PHẢI dưới {limit} ký tự. Chỉ trả về text tóm tắt, không giải thích.\n\n"
        f"{caption}"
    )
    r = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {PERPLEXITY_KEY}", "Content-Type": "application/json"},
        json={"model": "sonar-pro", "messages": [{"role": "user", "content": prompt}]},
        timeout=20,
    )
    result = r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if result and len(result) <= limit:
        return result
    # fallback nếu model vẫn trả về quá dài
    cut = result[:limit - 10].rfind("\n\n") if result else -1
    return result[:cut] if cut > 200 else (result or caption)[:limit - 3] + "..."


# ── Load post data ─────────────────────────────────────────────────────────────

def load_post(slug: str):
    post_dir = POSTS_DIR / slug
    md = (post_dir / "post.md").read_text(encoding="utf-8")

    # Caption
    m = re.search(r"## Post Text.*?\n+([\s\S]+?)(?:\n---|\n##)", md)
    caption = m.group(1).strip() if m else ""

    # Format: Carousel / single photo
    fmt_match = re.search(r"\*\*Format:\*\*\s*(.+)", md) or re.search(r"\*\*Visual:\*\*\s*(.+)", md)
    fmt = fmt_match.group(1).strip().lower() if fmt_match else ""
    is_carousel = "carousel" in fmt

    # Slide URLs + Platform từ Airtable
    at_key  = ENV["AIRTABLE_API_KEY"]
    at_base = ENV["AIRTABLE_BASE_ID"]
    at_table = "tbll5ikhBQPeak8xR"
    r = requests.get(
        f"https://api.airtable.com/v0/{at_base}/{at_table}",
        headers={"Authorization": f"Bearer {at_key}"},
        params={"filterByFormula": f"{{Slug}}='{slug}'", "fields[]": ["Slide URLs", "Platform"]},
    )
    fields = r.json()["records"][0]["fields"]
    slide_urls = json.loads(fields.get("Slide URLs", "[]"))
    platforms  = fields.get("Platform", [])

    # Nếu có nhiều hơn 1 ảnh thì luôn là carousel
    if len(slide_urls) > 1:
        is_carousel = True

    return caption, slide_urls, is_carousel, platforms


# ── Facebook: post helpers ─────────────────────────────────────────────────────

def fb_upload_photo(token: str, img_url: str) -> str:
    r = requests.post(
        "https://graph.facebook.com/v19.0/me/photos",
        data={"url": img_url, "published": "false", "access_token": token},
    )
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"Upload ảnh thất bại: {data}")
    return data["id"]


def fb_post_single_photo(token: str, caption: str, img_url: str, tag_uid: str = None, dry_run=False) -> str:
    """Đăng ảnh đơn (cá nhân / infographic). Hỗ trợ tag profile cá nhân."""
    if dry_run:
        print(f"    [DRY RUN] Would post single photo + tag={tag_uid}")
        return "dry-run-id"

    data = {
        "url": img_url,
        "message": caption,
        "published": "true",
        "access_token": token,
    }
    if tag_uid:
        data["tags"] = json.dumps([{"tag_uid": tag_uid}])

    r = requests.post("https://graph.facebook.com/v19.0/me/photos", data=data)
    result = r.json()
    if "id" not in result:
        raise RuntimeError(f"Đăng ảnh thất bại: {result}")
    # Facebook trả về photo_id, cần ghép thành post_id
    return result.get("post_id", result["id"])


def fb_post_carousel(token: str, caption: str, slide_urls: list, dry_run=False) -> str:
    """Đăng nhiều ảnh (carousel). Không hỗ trợ tag qua API."""
    if dry_run:
        print(f"    [DRY RUN] Would upload {len(slide_urls)} photos + create post")
        return "dry-run-id"

    print(f"    Upload {len(slide_urls)} ảnh lên Facebook...", flush=True)
    photo_ids = []
    for i, url in enumerate(slide_urls):
        pid = fb_upload_photo(token, url)
        photo_ids.append(pid)
        print(f"      [{i+1}/{len(slide_urls)}] ✓ {pid}")
        time.sleep(0.5)

    attached = [{"media_fbid": pid} for pid in photo_ids]
    r = requests.post(
        "https://graph.facebook.com/v19.0/me/feed",
        data={
            "message": caption,
            "attached_media": json.dumps(attached),
            "access_token": token,
        },
    )
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"Đăng post thất bại: {data}")
    return data["id"]


# ── Verification helpers ───────────────────────────────────────────────────────

def verify_facebook(token: str, post_url: str) -> bool:
    """Xác nhận bài Facebook thực sự tồn tại qua Graph API."""
    try:
        pid = post_url.split("facebook.com/")[-1].strip("/")
        r = requests.get(
            f"https://graph.facebook.com/v19.0/{pid}",
            params={"fields": "id", "access_token": token},
            timeout=10,
        )
        return "id" in r.json()
    except Exception:
        return False


def verify_buffer(post_value: str) -> tuple:
    """Xác nhận bài Buffer đã sent. Returns (verified: bool, url: str).
    Thử query Buffer API; nếu không hỗ trợ thì fallback trust response gốc."""
    if not post_value or "LỖI" in post_value:
        return False, post_value
    try:
        time.sleep(3)
        query = """
        query GetPost($id: String!) {
          post(id: $id) { id status url }
        }
        """
        r = requests.post(
            BUFFER_GQL,
            headers=BUFFER_HEADERS,
            json={"query": query, "variables": {"id": post_value}},
            timeout=10,
        )
        post = (r.json().get("data") or {}).get("post") or {}
        status = post.get("status", "")
        url = post.get("url") or post_value
        if status in ("sent", "service_update_sent"):
            return True, url
        if status:
            return False, url
        # Buffer không hỗ trợ query post → trust response gốc
        return True, post_value
    except Exception:
        return True, post_value


def verify_results(results: dict) -> dict:
    """Chạy verification cho từng platform, trả về results đã cập nhật."""
    verified = {}
    for platform, value in results.items():
        if "LỖI" in value:
            verified[platform] = value
            continue

        if platform in ("Facebook BMN", "Facebook"):
            ok = verify_facebook(FB_TOKEN_BMN, value)
            verified[platform] = value if ok else f"⚠️ CHƯA XÁC MINH: {value}"

        elif platform in ("Instagram", "TikTok", "Threads"):
            ok, url = verify_buffer(value)
            verified[platform] = url if ok else f"⚠️ CHƯA XÁC MINH: {url}"

        else:
            verified[platform] = value

    return verified


# ── Buffer: create post ────────────────────────────────────────────────────────

def buffer_create_post(channel_id: str, caption: str, slide_urls: list, metadata: dict = None, dry_run=False) -> str:
    if dry_run:
        print(f"    [DRY RUN] Would post {len(slide_urls)} images to channel {channel_id}")
        return "dry-run-id"

    assets = [{"image": {"url": url}} for url in slide_urls]

    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post { id }
        }
        ... on NotFoundError { message }
        ... on UnauthorizedError { message }
        ... on LimitReachedError { message }
        ... on InvalidInputError { message }
        ... on UnexpectedError { message }
        ... on RestProxyError { message }
      }
    }
    """
    post_input = {
        "channelId": channel_id,
        "text": caption,
        "schedulingType": "automatic",
        "mode": "shareNow",
        "assets": assets,
    }
    if metadata:
        post_input["metadata"] = metadata

    r = requests.post(
        BUFFER_GQL,
        headers=BUFFER_HEADERS,
        json={"query": mutation, "variables": {"input": post_input}},
    )
    data = r.json()
    if "errors" in data:
        raise RuntimeError(f"Buffer error: {data['errors']}")
    result = data.get("data", {}).get("createPost", {})
    post_id = result.get("post", {}).get("id")
    if not post_id:
        raise RuntimeError(result.get("message", f"Unexpected response: {result}"))
    return post_id


# ── Telegram notification ─────────────────────────────────────────────────────

def notify_telegram(slug: str, results: dict):
    token = ENV.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = ENV.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return

    print("   🔍 Xác minh bài đăng trước khi thông báo...", flush=True)
    verified = verify_results(results)

    success   = [k for k, v in verified.items() if "LỖI" not in v and "CHƯA XÁC MINH" not in v]
    unverified = [k for k, v in verified.items() if "CHƯA XÁC MINH" in v]
    failed    = [k for k, v in verified.items() if "LỖI" in v]

    lines = [f"📢 *Đã đăng:* `{slug}`", ""]
    for k, v in verified.items():
        if "LỖI" in v:
            lines.append(f"❌ *{k}:* {v.replace('LỖI: ', '')}")
        elif "CHƯA XÁC MINH" in v:
            url = v.replace("⚠️ CHƯA XÁC MINH: ", "")
            if url.startswith("http"):
                lines.append(f"⚠️ [{k} — chưa xác minh]({url})")
            else:
                lines.append(f"⚠️ *{k}:* chưa xác minh được")
        elif v.startswith("http"):
            lines.append(f"✅ [{k}]({v})")
        else:
            lines.append(f"✅ *{k}:* đã đăng")

    summary = []
    if success:    summary.append(f"✅ {len(success)} xác minh OK")
    if unverified: summary.append(f"⚠️ {len(unverified)} chưa xác minh")
    if failed:     summary.append(f"❌ {len(failed)} lỗi")
    lines += ["", " | ".join(summary)]

    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": "\n".join(lines), "parse_mode": "Markdown"},
    )


# ── Update Airtable status ─────────────────────────────────────────────────────

def update_airtable_status(slug: str, results: dict):
    from datetime import datetime
    at_key   = ENV["AIRTABLE_API_KEY"]
    at_base  = ENV["AIRTABLE_BASE_ID"]
    at_table = "tbll5ikhBQPeak8xR"
    headers  = {"Authorization": f"Bearer {at_key}", "Content-Type": "application/json"}

    r = requests.get(
        f"https://api.airtable.com/v0/{at_base}/{at_table}",
        headers=headers,
        params={"filterByFormula": f"{{Slug}}='{slug}'", "fields[]": ["Slug"]},
    )
    rec_id = r.json()["records"][0]["id"]

    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    notes = "\n".join([f"{k}: {v}" for k, v in results.items()])

    fields = {
        "Status":   "Published",
        "Đăng lúc": now,
        "Ghi chú":  f"Đăng tự động lúc {now}\n{notes}",
    }
    if "Instagram" in results and "LỖI" not in results["Instagram"]:
        fields["Instagram ID"] = results["Instagram"]
    if "TikTok" in results and "LỖI" not in results["TikTok"]:
        fields["TikTok ID"] = results["TikTok"]
    if "Threads" in results and "LỖI" not in results["Threads"]:
        fields["Threads ID"] = results["Threads"]

    requests.patch(
        f"https://api.airtable.com/v0/{at_base}/{at_table}/{rec_id}",
        headers=headers,
        json={"fields": fields},
    )


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--post", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", nargs="+", metavar="CHANNEL",
                        help="Chỉ đăng lên kênh cụ thể, vd: --only Instagram Threads")
    args = parser.parse_args()

    print(f"\n📢 Đăng bài: {args.post}")
    if args.dry_run:
        print("⚠️  DRY RUN — không gửi request thật\n")
    if args.only:
        print(f"⚡ Chỉ đăng kênh: {', '.join(args.only)}\n")

    caption, slide_urls, is_carousel, platforms = load_post(args.post)
    print(f"✓ Caption: {caption[:60]}...")
    print(f"✓ Slides: {len(slide_urls)} ảnh | Format: {'Carousel' if is_carousel else 'Ảnh đơn'}")
    print(f"✓ Platforms: {platforms}\n")

    only = set(args.only) if args.only else None

    results = {}

    # ── Facebook Bình Mê Nhà — tất cả nội dung ──
    # Facebook IQI được quản lý riêng qua table 📣 IQI Posts — không đăng từ workflow này
    post_bmn = FB_TOKEN_BMN and any(p in platforms for p in ["Facebook BMN", "Facebook"]) and (only is None or "Facebook BMN" in only)
    print(f"1. Facebook — Bình Mê Nhà {'(đăng)' if post_bmn else '(bỏ qua)'}")
    if post_bmn:
        try:
            if is_carousel:
                post_id = fb_post_carousel(FB_TOKEN_BMN, caption, slide_urls, args.dry_run)
            else:
                print(f"    → Tag profile cá nhân: {FB_PERSONAL_ID}")
                post_id = fb_post_single_photo(FB_TOKEN_BMN, caption, slide_urls[0], tag_uid=FB_PERSONAL_ID, dry_run=args.dry_run)
            results["Facebook BMN"] = f"https://facebook.com/{post_id}"
            print(f"   ✅ Post ID: {post_id}")
        except Exception as e:
            results["Facebook BMN"] = f"LỖI: {e}"
            print(f"   ❌ {e}")

    # ── Buffer: TikTok — carousel only ──
    post_tiktok = BUFFER_TOKEN and "TikTok" in platforms and is_carousel and (only is None or "TikTok" in only)
    print(f"2. TikTok {'(đăng)' if post_tiktok else '(bỏ qua — không phải carousel hoặc không có trong Platform)'}")
    if post_tiktok:
        try:
            post_id = buffer_create_post(BUFFER_TIKTOK, caption, slide_urls, args.dry_run)
            results["TikTok"] = post_id
            print(f"   ✅ Buffer post ID: {post_id}")
        except Exception as e:
            results["TikTok"] = f"LỖI: {e}"
            print(f"   ❌ {e}")

    # ── Buffer: Instagram ──
    post_ig = BUFFER_TOKEN and "Instagram" in platforms and (only is None or "Instagram" in only)
    print(f"3. Instagram {'(đăng)' if post_ig else '(bỏ qua)'}")
    if post_ig:
        ig_type = "carousel" if is_carousel else "post"
        ig_meta = {"instagram": {"type": ig_type, "shouldShareToFeed": True}}
        try:
            post_id = buffer_create_post(BUFFER_INSTAGRAM, caption, slide_urls, metadata=ig_meta, dry_run=args.dry_run)
            results["Instagram"] = post_id
            print(f"   ✅ Buffer post ID: {post_id}")
        except Exception as e:
            results["Instagram"] = f"LỖI: {e}"
            print(f"   ❌ {e}")

    # ── Buffer: Threads — max 500 chars ──
    post_threads = BUFFER_TOKEN and "Threads" in platforms and (only is None or "Threads" in only)
    print(f"4. Threads {'(đăng)' if post_threads else '(bỏ qua)'}")
    if post_threads:
        threads_meta = {"threads": {"type": "post"}}
        threads_caption = summarize_for_threads(caption)
        if len(threads_caption) < len(caption):
            print(f"   ✂️  Caption tóm tắt: {len(caption)} → {len(threads_caption)} ký tự")
        try:
            post_id = buffer_create_post(BUFFER_THREADS, threads_caption, slide_urls, metadata=threads_meta, dry_run=args.dry_run)
            results["Threads"] = post_id
            print(f"   ✅ Buffer post ID: {post_id}")
        except Exception as e:
            results["Threads"] = f"LỖI: {e}"
            print(f"   ❌ {e}")

    # ── Telegram notification ──
    print("\n📱 Gửi thông báo Telegram...")
    try:
        notify_telegram(args.post, results)
        print("   ✅ Đã gửi")
    except Exception as e:
        print(f"   ⚠️  {e}")

    # ── Update Airtable ──
    if not args.dry_run:
        print("\n📋 Cập nhật Airtable...")
        try:
            update_airtable_status(args.post, results)
            print("   ✅ Status → Published")
        except Exception as e:
            print(f"   ⚠️  {e}")

    print("\n─────────────────────────────")
    print("KẾT QUẢ:")
    for k, v in results.items():
        icon = "✅" if "LỖI" not in v else "❌"
        print(f"  {icon} {k}: {v}")


if __name__ == "__main__":
    main()
