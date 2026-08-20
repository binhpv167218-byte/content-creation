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
BUFFER_DANANGHOME_LINKEDIN  = "6a637b7de2638b94d7c8d08c"
BUFFER_DANANGHOME_GBP       = "6a54582b80cc80cdcaa92412"

# dananghome.com — Facebook Page: account Buffer RIÊNG (không chung org với 3 kênh trên),
# dùng token BUFFER_ACCESS_TOKEN_DANANGHOME_FB
BUFFER_DANANGHOME_FACEBOOK  = "6a86753cccaf649a67dd9b93"

# Facebook cá nhân Bình Mê Nhà — CÙNG account Buffer với Facebook DANANGHOME
# (cùng token BUFFER_ACCESS_TOKEN_DANANGHOME_FB, channel riêng). Thay thế hoàn
# toàn cách đăng cũ qua Graph API token FACEBOOK_TOKEN_BINH_ME_NHA (đã chết,
# app Meta bị xoá, code 190 — 2026-08-20).
BUFFER_BMN_FACEBOOK         = "6a86753cccaf649a67dd9b94"


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

def verify_buffer(buffer_token: str, post_value: str) -> tuple:
    """Returns (verified: bool, url: str)."""
    if not post_value or "LỖI" in post_value:
        return False, post_value
    query = """
    query GetPost($input: PostInput!) {
      post(input: $input) { id status error { message } }
    }
    """
    try:
        for wait_s in (5, 8, 13, 21, 30):  # "sending" là trạng thái transient, retry trước khi kết luận lỗi (tổng ~77s)
            time.sleep(wait_s)
            r = requests.post(
                BUFFER_GQL,
                headers={"Authorization": f"Bearer {buffer_token}", "Content-Type": "application/json"},
                json={"query": query, "variables": {"input": {"id": post_value}}},
                timeout=10,
            )
            post = (r.json().get("data") or {}).get("post") or {}
            status = post.get("status", "")
            err = (post.get("error") or {}).get("message", "")
            if status in ("sent", "service_update_sent"):
                return True, post_value
            if status and status != "sending":
                return False, f"{post_value} ({err or status})"
            if not status:
                return True, post_value  # Buffer không hỗ trợ query → trust
        return False, f"{post_value} ({status})"
    except Exception:
        return True, post_value


def verify_results(env: dict, results: dict) -> dict:
    buf       = env.get("BUFFER_ACCESS_TOKEN", "")
    buf_dh_fb = env.get("BUFFER_ACCESS_TOKEN_DANANGHOME_FB", "")
    verified = {}
    for platform, value in results.items():
        if "LỖI" in value:
            verified[platform] = value
            continue
        if platform in ("Facebook BMN", "Facebook DANANGHOME"):
            ok, url = verify_buffer(buf_dh_fb, value)
            verified[platform] = url if ok else f"⚠️ CHƯA XÁC MINH: {url}"
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

    records = []
    offset = None
    while True:
        params = {"fields[]": ["Slug", "Nội dung", "Nội dung BMN", "Slide URLs BMN", "Comment Text", "Tiêu đề", "Format", "Platform",
                                "Đăng lúc", "Ngày đăng", "Status", "Slide URLs", "Ảnh URL", "Ảnh",
                                "Link", "Board Id"]}
        if offset:
            params["offset"] = offset
        r = requests.get(
            f"https://api.airtable.com/v0/{at_base}/tbll5ikhBQPeak8xR",
            headers={"Authorization": f"Bearer {at_key}"},
            params=params,
            timeout=15,
        )
        if r.status_code != 200:
            raise RuntimeError(f"Airtable API lỗi {r.status_code}: {r.text[:200]}")
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"Airtable error: {data['error']}")
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
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


# ── Facebook video (qua Buffer) ──────────────────────────────────────────────

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

    notes    = "\n".join([f"{k}: {v}" for k, v in results.items()])
    # "CHƯA XÁC MINH" nghĩa là đã tạo bài thành công (có post ID), chỉ chưa kịp xác nhận Buffer
    # chuyển "sending" → "sent" trong lúc retry — KHÔNG phải lỗi thật, không được coi ngang LỖI.
    has_loi  = any("LỖI" in v for v in results.values())
    fields = {
        "Status":   "Lỗi" if has_loi else "Published",
        "Đăng lúc": now.strftime("%d/%m/%Y %H:%M"),
        "Ghi chú":  f"Tự đăng lúc {now.strftime('%d/%m/%Y %H:%M')}\n{notes}",
    }
    # Lưu platform IDs để evening summary có thể lấy link
    fb_url = results.get("Facebook BMN", "")
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
        headers=headers, json={"fields": fields, "typecast": True},
    )


# ── Telegram ──────────────────────────────────────────────────────────────────

def notify_telegram(env: dict, slug: str, verified: dict, title: str = "", link: str = ""):
    token   = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return

    now_vn = datetime.utcnow() + timedelta(hours=7)
    success    = sum(1 for v in verified.values() if "LỖI" not in v and "CHƯA XÁC MINH" not in v)
    unverified = sum(1 for v in verified.values() if "CHƯA XÁC MINH" in v)
    failed     = sum(1 for v in verified.values() if "LỖI" in v)

    lines = ["🏠 *DANANGHOME — Đăng bài tự động*", f"📝 {title or slug}"]
    if link:
        lines.append(f"🔗 [Xem bài viết]({link})")
    lines.append(f"🕐 {now_vn.strftime('%d/%m/%Y %H:%M')} · `{slug}`")
    lines.append("")
    lines.append("*Kênh:*")
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
    fields      = rec["fields"]
    caption     = fields.get("Nội dung", "")
    caption_bmn = fields.get("Nội dung BMN") or caption
    comment_text = fields.get("Comment Text", "")
    title      = fields.get("Tiêu đề", "")
    link       = fields.get("Link", "")
    board_id   = fields.get("Board Id", "")
    platforms  = fields.get("Platform", [])
    fmt        = fields.get("Format", "")
    slide_urls = json.loads(fields.get("Slide URLs", "[]"))
    slides_bmn_raw = fields.get("Slide URLs BMN", "")
    # Ảnh thật dự án, không lẫn slide 1 title card (chữ đè ảnh) của DANANGHOME
    slides_bmn = json.loads(slides_bmn_raw) if slides_bmn_raw else []
    if not slides_bmn:
        slides_bmn = slide_urls[1:] or slide_urls
    slides_bmn = slides_bmn[:1]  # BMN luôn 1 ảnh, không carousel

    # Ảnh attachment field — dùng cho Video Market khi Slide URLs rỗng
    anh_attachments = fields.get("Ảnh", []) or []
    anh_url = anh_attachments[0]["url"] if anh_attachments else fields.get("Ảnh URL", "")

    is_video    = fmt == "Video Market"
    is_carousel = len(slide_urls) > 1
    results = {}

    buf       = env.get("BUFFER_ACCESS_TOKEN", "")
    buf_dh_fb = env.get("BUFFER_ACCESS_TOKEN_DANANGHOME_FB", "")

    # ── Video Market ──────────────────────────────────────────────────────────
    if is_video and (slide_urls or anh_url):
        video_url = slide_urls[0] if slide_urls else anh_url
        if "Facebook BMN" in platforms and buf_dh_fb:
            try:
                pid = buffer_post_video(BUFFER_BMN_FACEBOOK, caption_bmn, video_url, buf_dh_fb, dry_run)
                results["Facebook BMN"] = pid
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
    # Facebook Bình Mê Nhà — qua Buffer, cùng account/token với Facebook DANANGHOME
    if "Facebook BMN" in platforms and buf_dh_fb:
        try:
            pid = buffer_post(BUFFER_BMN_FACEBOOK, caption_bmn, slides_bmn, buf_dh_fb,
                               metadata={"facebook": {"type": "post"}}, dry_run=dry_run)
            results["Facebook BMN"] = pid
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
    # Link CTA đã viết thẳng trong caption/text — không gửi kèm metadata.linkAttachment
    # vì Buffer/LinkedIn từ chối post vừa có ảnh (assets) vừa có linkAttachment.
    if "LinkedIn" in platforms and buf and anh_url:
        li_text = f"{title}\n\n{caption}" if title else caption
        try:
            pid = buffer_post(BUFFER_DANANGHOME_LINKEDIN, li_text, [anh_url], buf, dry_run=dry_run)
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

    # dananghome.com — Facebook Page (account Buffer riêng, token buf_dh_fb)
    if "Facebook DANANGHOME" in platforms and buf_dh_fb and (slide_urls or anh_url):
        fb_assets = slide_urls if slide_urls else [anh_url]
        fb_metadata = {"facebook": {"type": "post"}}
        if comment_text:
            fb_metadata["facebook"]["firstComment"] = comment_text
        try:
            pid = buffer_post(BUFFER_DANANGHOME_FACEBOOK, caption, fb_assets, buf_dh_fb,
                               metadata=fb_metadata, dry_run=dry_run)
            results["Facebook DANANGHOME"] = pid
        except Exception as e:
            results["Facebook DANANGHOME"] = f"LỖI: {e}"

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
                "fields[]": ["Slug", "Nội dung", "Nội dung BMN", "Slide URLs BMN", "Comment Text", "Tiêu đề", "Format", "Platform",
                             "Đăng lúc", "Ngày đăng", "Status", "Slide URLs", "Ảnh URL", "Ảnh",
                             "Link", "Board Id"]},
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

        if not results:
            print(f"  ⏭️  Platform không thuộc pipeline này ({rec['fields'].get('Platform')}) — bỏ qua, giữ Scheduled")
            continue

        for k, v in results.items():
            icon_r = "✅" if "LỖI" not in v else "❌"
            print(f"  {icon_r} {k}: {v}")

        if not args.dry_run:
            print(f"  🔍 Xác minh bài đăng...", flush=True)
            verified = verify_results(env, results)
            update_airtable(env, rec["id"], verified)
            notify_telegram(env, slug, verified,
                             title=rec["fields"].get("Tiêu đề", ""), link=rec["fields"].get("Link", ""))
            print(f"  📱 Telegram notified | Airtable updated")


if __name__ == "__main__":
    main()
