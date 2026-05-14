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

FORMAT_ICON = {"Ảnh cá nhân": "🖼", "Carousel": "📊", "AI Infographic": "📈"}

BUFFER_GQL       = "https://api.buffer.com/graphql"
BUFFER_TIKTOK    = "6a030a3f090476fb990f46e6"
BUFFER_INSTAGRAM = "6a033e20090476fb99104f87"
BUFFER_THREADS   = "6a030a61090476fb990f47b7"


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
    fb_iqi = env.get("FACEBOOK_TOKEN_BINH_PHAN_IQI", "")
    fb_bmn = env.get("FACEBOOK_TOKEN_BINH_ME_NHA", "")
    buf    = env.get("BUFFER_ACCESS_TOKEN", "")
    verified = {}
    for platform, value in results.items():
        if "LỖI" in value:
            verified[platform] = value
            continue
        if platform == "Facebook IQI":
            ok = verify_facebook(fb_iqi, value)
            verified[platform] = value if ok else f"⚠️ CHƯA XÁC MINH: {value}"
        elif platform in ("Facebook BMN", "Facebook"):
            ok = verify_facebook(fb_bmn, value)
            verified[platform] = value if ok else f"⚠️ CHƯA XÁC MINH: {value}"
        elif platform in ("Instagram", "TikTok", "Threads"):
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
    for key in [
        "AIRTABLE_API_KEY", "AIRTABLE_BASE_ID",
        "FACEBOOK_TOKEN_BINH_PHAN_IQI", "FACEBOOK_TOKEN_BINH_ME_NHA",
        "BUFFER_ACCESS_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    ]:
        if os.environ.get(key):
            env[key] = os.environ[key]
    return env


def get_due_posts(env: dict, now_vn: datetime, window_min=5, window_max=10) -> list:
    """Lấy bài Scheduled trong khoảng [now - window_min, now + window_max] phút."""
    window_start = now_vn - timedelta(minutes=window_min)
    window_end   = now_vn + timedelta(minutes=window_max)
    today        = now_vn.strftime("%Y-%m-%d")

    at_key  = env["AIRTABLE_API_KEY"]
    at_base = env["AIRTABLE_BASE_ID"]

    r = requests.get(
        f"https://api.airtable.com/v0/{at_base}/tbll5ikhBQPeak8xR",
        headers={"Authorization": f"Bearer {at_key}"},
        params={"fields[]": ["Slug", "Nội dung", "Format", "Platform",
                              "Đăng lúc", "Ngày đăng", "Status", "Slide URLs"]},
    )

    due = []
    for rec in r.json().get("records", []):
        f = rec["fields"]
        if f.get("Status") != "Scheduled":
            continue
        if f.get("Ngày đăng") != today:
            continue
        dang_luc = f.get("Đăng lúc", "")
        try:
            post_time = datetime.strptime(dang_luc, "%d/%m/%Y %H:%M")
            if window_start <= post_time <= window_end:
                due.append(rec)
        except ValueError:
            pass

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
    fb_iqi = results.get("Facebook IQI", "")
    if fb_iqi and "LỖI" not in fb_iqi:
        fields["Facebook ID"] = fb_iqi.replace("https://facebook.com/", "")
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
    platforms  = fields.get("Platform", [])
    slide_urls = json.loads(fields.get("Slide URLs", "[]"))

    is_carousel = len(slide_urls) > 1
    results = {}

    fb_iqi = env.get("FACEBOOK_TOKEN_BINH_PHAN_IQI", "")
    fb_bmn = env.get("FACEBOOK_TOKEN_BINH_ME_NHA", "")
    buf    = env.get("BUFFER_ACCESS_TOKEN", "")

    # Facebook Bình Phan IQI — chỉ đăng Dự án + Thị Trường
    # Nhận "Facebook IQI" (mới) hoặc "Facebook" (backward compat)
    post_iqi = fb_iqi and any(p in platforms for p in ["Facebook IQI", "Facebook"])
    if post_iqi:
        try:
            if is_carousel:
                pid = fb_post_carousel(fb_iqi, caption, slide_urls, dry_run)
            else:
                pid = fb_post_single(fb_iqi, caption, slide_urls[0], dry_run)
            results["Facebook IQI"] = f"https://facebook.com/{pid}"
        except Exception as e:
            results["Facebook IQI"] = f"LỖI: {e}"

    # Facebook Bình Mê Nhà — đăng tất cả loại nội dung
    # Nhận "Facebook BMN" (mới) hoặc "Facebook" (backward compat)
    post_bmn = fb_bmn and any(p in platforms for p in ["Facebook BMN", "Facebook"])
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
            pid = buffer_post(BUFFER_INSTAGRAM, caption, slide_urls, buf, dry_run)
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

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env    = load_env()
    now_vn = datetime.utcnow() + timedelta(hours=7)

    print(f"🕐 Kiểm tra lịch: {now_vn.strftime('%d/%m/%Y %H:%M')} (giờ VN)")

    due_posts = get_due_posts(env, now_vn)

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
