#!/usr/bin/env python3
"""
Kiểm tra Airtable và tự đăng bài theo lịch.
Chạy trên GitHub Actions mỗi 15 phút — không cần Mac bật.

Usage:
    python3 scripts/schedule_publish.py
    python3 scripts/schedule_publish.py --dry-run
"""

import json
import time
import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path

import requests

WORKSPACE = Path(__file__).parent.parent

FORMAT_ICON = {"Ảnh cá nhân": "🖼", "Carousel": "📊", "AI Infographic": "📈", "Video Market": "🎬"}

BUFFER_GQL       = "https://api.buffer.com/graphql"
BUFFER_TIKTOK    = "6a030a3f090476fb990f46e6"
BUFFER_INSTAGRAM = "6a033e20090476fb99104f87"
BUFFER_THREADS   = "6a030a61090476fb990f47b7"

# ── dananghome.com — Pinterest + LinkedIn + Google Business ─────────────────────
BUFFER_DANANGHOME_PINTEREST = "6a55ebc180cc80cdcaafd7e7"
BUFFER_DANANGHOME_LINKEDIN  = "6a55ebee80cc80cdcaafd85a"
BUFFER_DANANGHOME_GBP       = "6a54582b80cc80cdcaa92412"


def summarize_for_threads(caption: str, perplexity_key: str, limit: int = 490) -> str:
    """Dùng Perplexity sonar-pro tóm tắt caption xuống dưới `limit` ký tự."""
    if len(caption) <= limit:
        return caption

    if not perplexity_key:
        cut = caption[:limit - 10].rfind("\n\n")
        return caption[:cut] if cut > 200 else caption[:limit - 3] + "..."

    prompt = (
        f"Tóm tắt đoạn text sau thành phiên bản ngắn hơn, giữ nguyên giọng văn gốc "
        f"(xưng 'mình', tông trực tiếp, không corporate). "
        f"Kết quả PHẢI dưới {limit} ký tự. Chỉ trả về text tóm tắt, không giải thích.\n\n"
        f"{caption}"
    )
    try:
        r = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {perplexity_key}", "Content-Type": "application/json"},
            json={"model": "sonar-pro", "messages": [{"role": "user", "content": prompt}]},
            timeout=20,
        )
        result = r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        if result and len(result) <= limit:
            return result
        cut = result[:limit - 10].rfind("\n\n") if result else -1
        return result[:cut] if cut > 200 else (result or caption)[:limit - 3] + "..."
    except Exception:
        cut = caption[:limit - 10].rfind("\n\n")
        return caption[:cut] if cut > 200 else caption[:limit - 3] + "..."


# ── Verification helpers ───────────────────────────────────────────────────────

def verify_facebook(token: str, post_url: str) -> bool:
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


def verify_buffer(buffer_token: str, post_value: str) -> tuple:
    """Returns (verified: bool, url: str)."""
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
            headers={"Authorization": f"Bearer {buffer_token}", "Content-Type": "application/json"},
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
        return True, post_value  # Buffer không hỗ trợ query → trust
    except Exception:
        return True, post_value


def verify_results(env: dict, results: dict) -> dict:
    fb_bmn = env.get("FACEBOOK_TOKEN_BINH_ME_NHA", "")
    buf    = env.get("BUFFER_ACCESS_TOKEN", "")
    verified = {}
    for platform, value in results.items():
        if "LỖI" in value:
            verified[platform] = value
            continue
        if platform in ("BMN", "Facebook BMN", "Facebook", "FB Bình Phan"):
            ok = verify_facebook(fb_bmn, value)
            verified[platform] = value if ok else f"⚠️ CHƯA XÁC MINH: {value}"
        elif platform in ("Instagram", "TikTok", "Threads", "Pinterest", "LinkedIn", "GoogleBusiness"):
            ok, url = verify_buffer(buf, value)
            verified[platform] = url if ok else f"⚠️ CHƯA XÁC MINH: {url}"
        else:
            verified[platform] = value
    return verified


def load_env():
    env = {}
    env_file = WORKSPACE / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    # Đọc tất cả env vars từ os.environ (GitHub Actions secrets)
    env.update({k: v for k, v in os.environ.items() if v and k.isupper()})
    return env


def get_due_posts(env: dict, now_vn: datetime, window_max=10) -> list:
    """
    Catch-up mode: lấy TẤT CẢ bài Scheduled hôm nay đã qua giờ đăng (hoặc sắp đến).
    Không dùng window_min — GitHub Actions chạy muộn vẫn pick up được bài bị bỏ lọt.
    Dedup an toàn: bài đã đăng → Status=Published → không bao giờ bị chọn lại.
    """
    window_end = now_vn + timedelta(minutes=window_max)
    today      = now_vn.strftime("%Y-%m-%d")

    at_key  = env["AIRTABLE_API_KEY"]
    at_base = env["AIRTABLE_BASE_ID"]

    r = requests.get(
        f"https://api.airtable.com/v0/{at_base}/tbll5ikhBQPeak8xR",
        headers={"Authorization": f"Bearer {at_key}"},
        params={"fields[]": ["Slug", "Nội dung", "Tiêu đề", "Format", "Platform",
                              "Đăng lúc", "Ngày đăng", "Status", "Slide URLs", "Ảnh URL", "Ảnh",
                              "Link", "Board Id"]},
        timeout=15,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Airtable API lỗi {r.status_code}: {r.text[:200]}")
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"Airtable error: {data['error']}")
    records = data.get("records", [])
    if not records:
        print(f"  ℹ️  Airtable trả về 0 records (tổng bảng có thể trống)")

    due = []
    for rec in records:
        f = rec["fields"]
        if f.get("Status") != "Scheduled":
            continue
        if f.get("Ngày đăng") != today:
            continue
        dang_luc = f.get("Đăng lúc", "")
        try:
            post_time = datetime.strptime(dang_luc, "%d/%m/%Y %H:%M")
            # Catch-up: đăng nếu đã qua giờ hoặc sắp đến (trong window_max phút)
            if post_time <= window_end:
                late_min = int((now_vn - post_time).total_seconds() / 60)
                if late_min > 15:
                    print(f"  ⚠️  Bài muộn {late_min} phút: {f.get('Slug')} ({dang_luc})")
                due.append(rec)
        except ValueError:
            pass

    # Sắp xếp theo giờ đăng — đăng bài sớm nhất trước
    due.sort(key=lambda r: r["fields"].get("Đăng lúc", ""))
    return due


# ── Facebook helpers ──────────────────────────────────────────────────────────

def fb_upload_photo(token: str, img_url: str) -> str:
    r = requests.post(
        "https://graph.facebook.com/v19.0/me/photos",
        data={"url": img_url, "published": "false", "access_token": token},
    )
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"Upload ảnh thất bại: {data}")
    return data["id"]


def fb_post_single(token: str, caption: str, img_url: str, dry_run=False) -> str:
    if dry_run:
        return "dry-run-single"
    r = requests.post(
        "https://graph.facebook.com/v19.0/me/photos",
        data={"url": img_url, "message": caption, "published": "true", "access_token": token},
    )
    result = r.json()
    if "id" not in result:
        raise RuntimeError(f"Đăng ảnh thất bại: {result}")
    return result.get("post_id", result["id"])


def fb_post_carousel(token: str, caption: str, slide_urls: list, dry_run=False) -> str:
    if dry_run:
        return "dry-run-carousel"
    photo_ids = []
    for url in slide_urls:
        pid = fb_upload_photo(token, url)
        photo_ids.append(pid)
        time.sleep(0.5)
    attached = [{"media_fbid": pid} for pid in photo_ids]
    r = requests.post(
        "https://graph.facebook.com/v19.0/me/feed",
        data={"message": caption, "attached_media": json.dumps(attached), "access_token": token},
    )
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"Đăng carousel thất bại: {data}")
    return data["id"]


# ── Buffer helper ─────────────────────────────────────────────────────────────

def buffer_post(channel_id: str, caption: str, slide_urls: list, buffer_token: str, metadata: dict = None, dry_run=False) -> str:
    if dry_run:
        return "dry-run-buffer"
    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess { post { id } }
        ... on NotFoundError { message }
        ... on UnauthorizedError { message }
        ... on LimitReachedError { message }
        ... on InvalidInputError { message }
        ... on UnexpectedError { message }
        ... on RestProxyError { message }
      }
    }
    """
    assets = [{"image": {"url": url}} for url in slide_urls]
    post_input = {
        "channelId": channel_id, "text": caption,
        "schedulingType": "automatic", "mode": "shareNow", "assets": assets,
    }
    if metadata:
        post_input["metadata"] = metadata

    r = requests.post(
        BUFFER_GQL,
        headers={"Authorization": f"Bearer {buffer_token}", "Content-Type": "application/json"},
        json={"query": mutation, "variables": {"input": post_input}},
    )
    data = r.json()
    if "errors" in data:
        raise RuntimeError(f"Buffer error: {data['errors']}")
    result = data.get("data", {}).get("createPost", {})
    post   = result.get("post", {})
    post_id = post.get("id")
    if not post_id:
        raise RuntimeError(result.get("message", f"Unexpected response: {result}"))
    return post.get("url") or post_id


# ── Facebook video ────────────────────────────────────────────────────────────

def fb_post_video(token: str, caption: str, video_url: str, dry_run=False) -> str:
    if dry_run:
        return "dry-run-video"
    data = {
        "file_url": video_url,
        "description": caption,
        "published": "true",
        "access_token": token,
    }
    r = requests.post("https://graph.facebook.com/v19.0/me/videos", data=data, timeout=60)
    result = r.json()
    if "id" not in result:
        raise RuntimeError(f"FB video lỗi: {result}")
    return result.get("post_id", result["id"])


def buffer_post_video(channel_id: str, caption: str, video_url: str, buffer_token: str, dry_run=False) -> str:
    if dry_run:
        return "dry-run-buffer-video"
    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess { post { id } }
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
        "channelId": channel_id, "text": caption,
        "schedulingType": "automatic", "mode": "shareNow",
        "assets": [{"video": {"url": video_url}}],
    }
    r = requests.post(
        BUFFER_GQL,
        headers={"Authorization": f"Bearer {buffer_token}", "Content-Type": "application/json"},
        json={"query": mutation, "variables": {"input": post_input}},
    )
    data = r.json()
    if "errors" in data:
        raise RuntimeError(f"Buffer video error: {data['errors']}")
    result = data.get("data", {}).get("createPost", {})
    post_id = result.get("post", {}).get("id")
    if not post_id:
        raise RuntimeError(result.get("message", f"Unexpected: {result}"))
    return post_id


# ── Airtable update ───────────────────────────────────────────────────────────

def update_airtable(env: dict, rec_id: str, results: dict):
    at_key  = env["AIRTABLE_API_KEY"]
    at_base = env["AIRTABLE_BASE_ID"]
    headers = {"Authorization": f"Bearer {at_key}", "Content-Type": "application/json"}
    now     = datetime.utcnow() + timedelta(hours=7)  # Vietnam time

    notes = "\n".join([f"{k}: {v}" for k, v in results.items()])
    fields = {
        "Status":   "Published",
        "Đăng lúc": now.strftime("%d/%m/%Y %H:%M"),
        "Ghi chú":  f"Tự đăng lúc {now.strftime('%d/%m/%Y %H:%M')}\n{notes}",
    }
    # Lưu platform IDs để evening summary có thể lấy link
    fb_url = results.get("Facebook BMN", results.get("FB Bình Phan", results.get("Facebook", "")))
    if fb_url and "LỖI" not in fb_url and "facebook.com/" in fb_url:
        fields["Facebook ID"] = fb_url.split("facebook.com/")[-1].strip("/")
    if "Instagram" in results and "LỖI" not in results["Instagram"]:
        fields["Instagram ID"] = results["Instagram"]
    if "TikTok" in results and "LỖI" not in results["TikTok"]:
        fields["TikTok ID"] = results["TikTok"]
    if "Threads" in results and "LỖI" not in results["Threads"]:
        fields["Threads ID"] = results["Threads"]
    requests.patch(
        f"https://api.airtable.com/v0/{at_base}/tbll5ikhBQPeak8xR/{rec_id}",
        headers=headers, json={"fields": fields},
    )


# ── Telegram ──────────────────────────────────────────────────────────────────

def notify_telegram(env: dict, slug: str, results: dict):
    token   = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return

    print(f"  🔍 Xác minh bài đăng...", flush=True)
    verified = verify_results(env, results)

    success    = sum(1 for v in verified.values() if "LỖI" not in v and "CHƯA XÁC MINH" not in v)
    unverified = sum(1 for v in verified.values() if "CHƯA XÁC MINH" in v)
    failed     = sum(1 for v in verified.values() if "LỖI" in v)

    lines = [f"📢 *Đã đăng tự động:* `{slug}`", ""]
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
    if success:    summary.append(f"✅ {success} xác minh OK")
    if unverified: summary.append(f"⚠️ {unverified} chưa xác minh")
    if failed:     summary.append(f"❌ {failed} lỗi")
    lines += ["", " | ".join(summary)]

    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": "\n".join(lines), "parse_mode": "Markdown"},
    )


# ── Publish 1 post ────────────────────────────────────────────────────────────

def publish_post(env: dict, rec: dict, dry_run=False) -> dict:
    fields     = rec["fields"]
    caption    = fields.get("Nội dung", "")
    title      = fields.get("Tiêu đề", "")
    link       = fields.get("Link", "")
    board_id   = fields.get("Board Id", "")
    platforms  = fields.get("Platform", [])
    fmt        = fields.get("Format", "")
    slide_urls = json.loads(fields.get("Slide URLs", "[]"))

    # Ảnh attachment field — dùng cho Video Market khi Slide URLs rỗng
    anh_attachments = fields.get("Ảnh", []) or []
    anh_url = anh_attachments[0]["url"] if anh_attachments else fields.get("Ảnh URL", "")

    is_video    = fmt == "Video Market"
    is_carousel = len(slide_urls) > 1
    results = {}

    fb_bmn = env.get("FACEBOOK_TOKEN_BINH_ME_NHA", "")
    buf    = env.get("BUFFER_ACCESS_TOKEN", "")

    # ── Video Market ──────────────────────────────────────────────────────────
    if is_video and (slide_urls or anh_url):
        video_url = slide_urls[0] if slide_urls else anh_url
        if fb_bmn and any(p in platforms for p in ["BMN", "Facebook BMN", "Facebook", "FB Bình Phan"]):
            try:
                pid = fb_post_video(fb_bmn, caption, video_url, dry_run)
                results["Facebook BMN"] = f"https://facebook.com/{pid}"
            except Exception as e:
                results["Facebook BMN"] = f"LỖI: {e}"
        if "TikTok" in platforms and buf:
            try:
                pid = buffer_post_video(BUFFER_TIKTOK, caption, video_url, buf, dry_run)
                results["TikTok"] = pid
            except Exception as e:
                results["TikTok"] = f"LỖI: {e}"
        return results

    # ── Image / Carousel ─────────────────────────────────────────────────────
    # Facebook Bình Mê Nhà — đăng tất cả loại nội dung
    # Nhận "Facebook BMN" / "FB Bình Phan" (mới) hoặc "Facebook" (backward compat)
    post_bmn = fb_bmn and any(p in platforms for p in ["BMN", "Facebook BMN", "Facebook", "FB Bình Phan"])
    if post_bmn:
        try:
            if is_carousel:
                pid = fb_post_carousel(fb_bmn, caption, slide_urls, dry_run)
            else:
                pid = fb_post_single(fb_bmn, caption, slide_urls[0], dry_run)
            results["Facebook BMN"] = f"https://facebook.com/{pid}"
        except Exception as e:
            results["Facebook BMN"] = f"LỖI: {e}"

    # TikTok (carousel only)
    if "TikTok" in platforms and is_carousel and buf:
        try:
            pid = buffer_post(BUFFER_TIKTOK, caption, slide_urls, buf, dry_run)
            results["TikTok"] = pid
        except Exception as e:
            results["TikTok"] = f"LỖI: {e}"

    # Instagram (không đăng dự án)
    if "Instagram" in platforms and buf:
        try:
            pid = buffer_post(BUFFER_INSTAGRAM, caption, slide_urls, buf,
                              metadata={"instagram": {"type": "post", "shouldShareToFeed": True}}, dry_run=dry_run)
            results["Instagram"] = pid
        except Exception as e:
            results["Instagram"] = f"LỖI: {e}"

    # Threads (không đăng dự án) — max 500 chars, tóm tắt nếu cần
    if "Threads" in platforms and buf:
        threads_caption = summarize_for_threads(caption, env.get("PERPLEXITY_API_KEY", ""))
        try:
            pid = buffer_post(BUFFER_THREADS, threads_caption, slide_urls, buf, metadata={"threads": {"type": "post"}}, dry_run=dry_run)
            results["Threads"] = pid
        except Exception as e:
            results["Threads"] = f"LỖI: {e}"

    # dananghome.com — Pinterest
    if "Pinterest" in platforms and buf and anh_url:
        try:
            pid = buffer_post(BUFFER_DANANGHOME_PINTEREST, caption, [anh_url], buf,
                               metadata={"pinterest": {"title": title, "url": link, "boardServiceId": board_id}},
                               dry_run=dry_run)
            results["Pinterest"] = pid
        except Exception as e:
            results["Pinterest"] = f"LỖI: {e}"

    # dananghome.com — LinkedIn
    if "LinkedIn" in platforms and buf and anh_url:
        li_text = f"{title}\n\n{caption}" if title else caption
        try:
            pid = buffer_post(BUFFER_DANANGHOME_LINKEDIN, li_text, [anh_url], buf,
                               metadata={"linkedin": {"linkAttachment": {"url": link}}},
                               dry_run=dry_run)
            results["LinkedIn"] = pid
        except Exception as e:
            results["LinkedIn"] = f"LỖI: {e}"

    # dananghome.com — Google Business Profile
    if "GoogleBusiness" in platforms and buf and anh_url:
        try:
            pid = buffer_post(BUFFER_DANANGHOME_GBP, caption, [anh_url], buf,
                               metadata={"google": {"type": "whats_new",
                                                     "detailsWhatsNew": {"button": "learn_more", "link": link}}},
                               dry_run=dry_run)
            results["GoogleBusiness"] = pid
        except Exception as e:
            results["GoogleBusiness"] = f"LỖI: {e}"

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def get_posts_by_slug(env: dict, slugs: list) -> list:
    """Lấy records theo slug — dùng cho --force."""
    at_key  = env["AIRTABLE_API_KEY"]
    at_base = env["AIRTABLE_BASE_ID"]
    formula = "OR(" + ",".join(f"{{Slug}}='{s}'" for s in slugs) + ")"
    r = requests.get(
        f"https://api.airtable.com/v0/{at_base}/tbll5ikhBQPeak8xR",
        headers={"Authorization": f"Bearer {at_key}"},
        params={"filterByFormula": formula,
                "fields[]": ["Slug", "Nội dung", "Format", "Platform",
                             "Đăng lúc", "Ngày đăng", "Status", "Slide URLs", "Ảnh URL", "Ảnh"]},
    )
    return r.json().get("records", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", nargs="+", metavar="SLUG",
                        help="Force-publish specific slugs bất kể ngày/giờ")
    args = parser.parse_args()

    env = load_env()

    if args.force:
        due_posts = get_posts_by_slug(env, args.force)
        now_vn = datetime.utcnow() + timedelta(hours=7)
        print(f"⚡ Force mode: {args.force}")
    else:
        # Random delay ±200s: trigger sớm 200s, ngủ thêm 0–400s ngẫu nhiên
        if not args.dry_run:
            import random
            delay = random.randint(0, 400)
            print(f"⏱  Jitter: {delay}s ({delay//60}m{delay%60:02d}s) — tránh pattern cố định")
            time.sleep(delay)

        now_vn = datetime.utcnow() + timedelta(hours=7)
        due_posts = get_due_posts(env, now_vn, window_max=10)

    print(f"🕐 Kiểm tra lịch: {now_vn.strftime('%d/%m/%Y %H:%M:%S')} (giờ VN)")

    if not due_posts:
        print("✓ Không có bài nào cần đăng lúc này.")
        return

    print(f"📋 Tìm thấy {len(due_posts)} bài cần đăng:")
    for rec in due_posts:
        f = rec["fields"]
        print(f"  → [{f.get('Đăng lúc')}] {f.get('Slug')} | {f.get('Format')} | {f.get('Platform')}")

    if args.dry_run:
        print("\n⚠️  DRY RUN — không gửi request thật")

    for rec in due_posts:
        slug = rec["fields"].get("Slug", "unknown")
        fmt  = rec["fields"].get("Format", "")
        icon = FORMAT_ICON.get(fmt, "📝")
        print(f"\n{icon} Đăng: {slug}")

        results = publish_post(env, rec, args.dry_run)

        for k, v in results.items():
            icon_r = "✅" if "LỖI" not in v else "❌"
            print(f"  {icon_r} {k}: {v}")

        if not args.dry_run:
            update_airtable(env, rec["id"], results)
            notify_telegram(env, slug, results)
            print(f"  📱 Telegram notified | Airtable updated")


if __name__ == "__main__":
    main()
