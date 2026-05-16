#!/usr/bin/env python3
"""
Đăng bài tự động lên page Bình Phan IQI — 12 bài/ngày.
Trigger bởi cron-job.org mỗi 30 phút → GitHub Actions workflow_dispatch.
Script tự detect slot trong window 30 phút + jitter 0–400s ngẫu nhiên.

Cấu trúc 12 slot/ngày:
  4x P1  Sun Symphony 5 (đang nhận booking): 07:00 | 08:30* | 17:30 | 21:00
           * 08:30: bắt buộc có CTA booking trong Ghi Chú
  6x P2  Capital Square, FourS Tower, Newtown Diamond (mở bán + có giỏ hàng):
           09:30 CS dự án | 10:30 CS giỏ hàng
           11:30 FT dự án | 12:30 FT giỏ hàng
           13:30 ND dự án | 14:30 ND giỏ hàng
  2x P3/P4  Vinhomes HVB, M Landmark, Nobu, The Legend City (rotate mỗi ngày):
           16:00 project A | 19:00 project B

Slot giỏ hàng (p2_X_gh):
  - Loại căn xoay mỗi ngày: 1PN+ → 2PN → 3PN (date.toordinal() % 3)
  - Dữ liệu lấy TRỰC TIẾP từ GH tables (không cần pre-write trong IQI Posts)
  - Caption tự generate từ các căn Còn hàng + giá

Không đăng Infographic. Chỉ Photo và Carousel.

Usage:
    python3 scripts/schedule_publish_iqi.py
    python3 scripts/schedule_publish_iqi.py --dry-run
"""

import argparse
import json
import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

WORKSPACE = Path(__file__).parent.parent

# ── Airtable IDs ──────────────────────────────────────────────────────────────
IQI_TABLE = "tblhLcemzxd9H0aHF"
GH_TABLES = {
    "Capital Square":  "tblnV7Axd5kXhJE5E",
    "FourS Tower":     "tblyJ7vOHHHGJPZ10",
    "Newtown Diamond": "tblknwx3SEzz1lxrk",
}

# Cấu hình từng GH table: field tên loại căn và field giá chính
# cover_paths: dict loại căn → đường dẫn ảnh local (relative từ WORKSPACE)
# "default" dùng khi không match loại căn cụ thể. Để "" = text-only post.
GH_CONFIG = {
    "Capital Square": {
        "unit_field": "Số PN",
        "price_field": "Giá TT Chuẩn",
        "area_field":  "DT Căn Hộ (m²)",
        "status_field": "Tình Trạng",
        "status_ok": ["Còn hàng"],
        "cover_paths": {"default": ""},   # chưa có ảnh, text-only
    },
    "FourS Tower": {
        "unit_field": "Loại Căn",
        "price_field": "Giá VAT+KPBT",
        "area_field":  "Tổng DT (m²)",
        "status_field": "Tình Trạng",
        "status_ok": ["Còn hàng", "Độc quyền"],
        "cover_paths": {
            "1PN+": "context/images/projects/fours-tower/fours-mat-bang-can-ho-1pn-plus-53m2.jpg",
            "2PN":  "context/images/projects/fours-tower/fours-mat-bang-can-ho-2pn-73m2.jpg",
            "3PN":  "context/images/projects/fours-tower/fours-mat-bang-can-ho-3pn-103m2.jpg",
            "default": "context/images/projects/fours-tower/fours-phoi-canh-hai-toa-thap-doc-dai-lo.jpg",
        },
    },
    "Newtown Diamond": {
        "unit_field": "Số PN",
        "price_field": "Giá TT Chuẩn",
        "area_field":  "DT Thông Thủy (m²)",
        "status_field": "Tình Trạng",
        "status_ok": ["Còn hàng"],
        "cover_paths": {"default": ""},   # chưa có ảnh, text-only
    },
}


def get_cover_path(project, unit_type):
    """Trả về đường dẫn ảnh local cho giỏ hàng post, hoặc '' nếu không có."""
    paths = GH_CONFIG[project].get("cover_paths", {})
    path = paths.get(unit_type) or paths.get("default", "")
    if not path:
        return ""
    full = WORKSPACE / path
    return str(full) if full.exists() else ""

# ── Rotation ──────────────────────────────────────────────────────────────────
UNIT_CYCLE = ["1PN+", "2PN", "3PN"]

# Mapping loại căn cycle → giá trị thực trong GH tables
UNIT_ALIASES = {
    "1PN+": ["1PN", "1BR", "1BR+", "1PN+"],
    "2PN":  ["2PN", "2BR", "2PN+1"],
    "3PN":  ["3PN", "3BR"],
}

# P3/P4 xoay — 2 project/ngày (slot 16:00 và 19:00)
P3_P4_CYCLE = [
    "Vinhomes Hải Vân Bay",
    "M Landmark",
    "Nobu Residences",
    "The Legend City",
]

P1_PROJECT  = "Sun Symphony 5"
P2_PROJECTS = {
    "cs": "Capital Square",
    "ft": "FourS Tower",
    "nd": "Newtown Diamond",
}

# ── 12 Daily Slots ────────────────────────────────────────────────────────────
DAILY_SLOTS = [
    ("07:00", "p1"),
    ("08:30", "p1_cta"),
    ("09:30", "p2_cs_da"),
    ("10:30", "p2_cs_gh"),
    ("11:30", "p2_ft_da"),
    ("12:30", "p2_ft_gh"),
    ("13:30", "p2_nd_da"),
    ("14:30", "p2_nd_gh"),
    ("16:00", "p3p4_a"),
    ("17:30", "p1"),
    ("19:00", "p3p4_b"),
    ("21:00", "p1"),
]


# ── Env ───────────────────────────────────────────────────────────────────────

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


# ── Rotation helpers ──────────────────────────────────────────────────────────

def get_today_context(today):
    idx       = today.toordinal()
    unit_type = UNIT_CYCLE[idx % len(UNIT_CYCLE)]
    a_idx     = (idx * 2)     % len(P3_P4_CYCLE)
    b_idx     = (idx * 2 + 1) % len(P3_P4_CYCLE)
    return {
        "unit_type":    unit_type,
        "unit_aliases": UNIT_ALIASES[unit_type],
        "p3p4_a":       P3_P4_CYCLE[a_idx],
        "p3p4_b":       P3_P4_CYCLE[b_idx],
    }


def slot_meta(slot_type, ctx):
    mapping = {
        "p1":       (P1_PROJECT,        "du_an",   None,             False),
        "p1_cta":   (P1_PROJECT,        "du_an",   None,             True),
        "p2_cs_da": (P2_PROJECTS["cs"], "du_an",   None,             False),
        "p2_cs_gh": (P2_PROJECTS["cs"], "gio_hang",ctx["unit_type"], False),
        "p2_ft_da": (P2_PROJECTS["ft"], "du_an",   None,             False),
        "p2_ft_gh": (P2_PROJECTS["ft"], "gio_hang",ctx["unit_type"], False),
        "p2_nd_da": (P2_PROJECTS["nd"], "du_an",   None,             False),
        "p2_nd_gh": (P2_PROJECTS["nd"], "gio_hang",ctx["unit_type"], False),
        "p3p4_a":   (ctx["p3p4_a"],     "du_an",   None,             False),
        "p3p4_b":   (ctx["p3p4_b"],     "du_an",   None,             False),
    }
    project, content, unit, is_cta = mapping[slot_type]
    return {"project": project, "content": content,
            "unit_type": unit, "is_cta": is_cta}


# ── Slot scheduling ───────────────────────────────────────────────────────────

def get_due_slots(now_vn, window_min=30, window_max=5):
    """
    Tìm slot trong [now - window_min, now + window_max] phút.
    window_min=30 phù hợp với cron-job.org trigger mỗi 30 phút.
    Các slot cách nhau tối thiểu 60 phút → không overlap.
    """
    ws = now_vn - timedelta(minutes=window_min)
    we = now_vn + timedelta(minutes=window_max)
    due = []
    for slot_time_str, slot_type in DAILY_SLOTS:
        h, m = map(int, slot_time_str.split(":"))
        slot_dt = now_vn.replace(hour=h, minute=m, second=0, microsecond=0)
        if ws <= slot_dt <= we:
            due.append((slot_time_str, slot_type))
    return due


# ── Airtable: dự án posts ─────────────────────────────────────────────────────

def find_du_an_post(at_key, at_base, project, prefer_cta=False):
    """Tìm bài Sẵn sàng trong IQI Posts cho slot dự án."""
    def query(cta_only=False):
        parts = [
            f"{{Dự Án}}='{project}'",
            "{Trạng Thái}='Sẵn sàng'",
            "NOT(OR({Format}='Infographic', {Format}='AI Infographic'))",
        ]
        if cta_only:
            parts.append("FIND('CTA', {Ghi Chú})")
        formula = "AND(" + ", ".join(parts) + ")"
        r = requests.get(
            f"https://api.airtable.com/v0/{at_base}/{IQI_TABLE}",
            headers={"Authorization": f"Bearer {at_key}"},
            params={
                "filterByFormula": formula,
                "maxRecords": 1,
                "sort[0][field]": "Ngày Đăng",
                "sort[0][direction]": "asc",
                "fields[]": ["Tiêu Đề / Hook", "Caption", "Format",
                             "Slide URLs", "Ghi Chú"],
            },
        )
        recs = r.json().get("records", [])
        return recs[0] if recs else None

    if prefer_cta:
        post = query(cta_only=True)
        if post:
            return post
    return query(cta_only=False)


# ── Airtable: giỏ hàng từ GH table ──────────────────────────────────────────

def fetch_gio_hang(at_key, at_base, project, unit_type):
    """
    Lấy danh sách căn Còn hàng thuộc loại unit_type từ GH table.
    Trả về list dict với thông tin căn + giá.
    """
    cfg        = GH_CONFIG[project]
    table_id   = GH_TABLES[project]
    unit_field = cfg["unit_field"]
    aliases    = UNIT_ALIASES[unit_type]

    # Filter: Tình Trạng còn hàng + loại căn khớp
    status_filters = [f"{{Tình Trạng}}='{s}'" for s in cfg["status_ok"]]
    unit_filters   = [f"{{{unit_field}}}='{a}'" for a in aliases]

    formula = (
        f"AND(OR({', '.join(status_filters)}), "
        f"OR({', '.join(unit_filters)}))"
    )

    fields = ["Mã Căn", unit_field, cfg["price_field"], cfg["area_field"],
              cfg["status_field"]]
    if project == "FourS Tower":
        fields += ["Tòa", "Hướng"]
    else:
        fields += ["Tòa", "Tầng"]

    r = requests.get(
        f"https://api.airtable.com/v0/{at_base}/{table_id}",
        headers={"Authorization": f"Bearer {at_key}"},
        params={"filterByFormula": formula, "fields[]": fields,
                "maxRecords": 10},
    )
    return r.json().get("records", [])


def format_price(value):
    """Định dạng giá tỷ đồng. Ví dụ: 3500000000 → '3,5 tỷ'."""
    if not value:
        return "Liên hệ"
    ty = value / 1_000_000_000
    if ty >= 1:
        return f"{ty:,.1f} tỷ".replace(",", ".")
    trieu = value / 1_000_000
    return f"{trieu:,.0f} triệu"


def build_gio_hang_caption(project, unit_type, records, cfg):
    """Tạo caption từ danh sách căn."""
    if not records:
        return None

    today_str = datetime.utcnow().strftime("%d/%m/%Y")
    lines = [
        f"🏠 GIỎ HÀNG {project.upper()} — {unit_type} ({today_str})",
        "",
    ]

    for rec in records[:6]:     # tối đa 6 căn để không quá dài
        f = rec["fields"]
        ma_can   = f.get("Mã Căn", "")
        unit_val = f.get(cfg["unit_field"], unit_type)
        area     = f.get(cfg["area_field"], "")
        price    = format_price(f.get(cfg["price_field"]))
        toa      = f.get("Tòa", "")
        tang     = f.get("Tầng", "") or f.get("Hướng", "")

        detail = f"Tòa {toa}" if toa else ""
        if tang:
            detail += f" | {('Tầng ' + str(tang)) if isinstance(tang, (int, float)) else tang}"

        lines.append(f"▸ {ma_can}  {unit_val}  {area}m²  →  {price}")
        if detail.strip():
            lines.append(f"   {detail.strip()}")

    total = len(records)
    if total > 6:
        lines.append(f"\n+ {total - 6} căn khác — nhắn Bình để xem đầy đủ.")
    else:
        lines.append(f"\nCòn {total} căn. Nhắn Bình để xem chi tiết + chính sách.")

    lines += [
        "",
        "#BinhPhanBDS #IQI #BDS #DaNang",
    ]
    return "\n".join(lines)


# ── Facebook posting ──────────────────────────────────────────────────────────

def fb_upload_photo(token, img_url):
    r = requests.post(
        "https://graph.facebook.com/v19.0/me/photos",
        data={"url": img_url, "published": "false", "access_token": token},
    )
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"Upload ảnh thất bại: {data}")
    return data["id"]


def fb_upload_local_photo(token, file_path):
    """Upload ảnh từ file local lên Facebook (unpublished)."""
    with open(file_path, "rb") as f:
        r = requests.post(
            "https://graph.facebook.com/v19.0/me/photos",
            data={"published": "false", "access_token": token},
            files={"source": f},
        )
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"Upload ảnh local thất bại: {data}")
    return data["id"]


def fb_post_single(token, caption, img_url, dry_run=False):
    if dry_run:
        return "dry-run-single"
    r = requests.post(
        "https://graph.facebook.com/v19.0/me/photos",
        data={"url": img_url, "message": caption,
              "published": "true", "access_token": token},
    )
    result = r.json()
    if "id" not in result:
        raise RuntimeError(f"Đăng ảnh thất bại: {result}")
    return result.get("post_id", result["id"])


def fb_post_with_local_image(token, caption, file_path, dry_run=False):
    """Upload ảnh local rồi đăng kèm caption lên feed."""
    if dry_run:
        return "dry-run-local-image"
    photo_id = fb_upload_local_photo(token, file_path)
    r = requests.post(
        "https://graph.facebook.com/v19.0/me/feed",
        data={
            "message": caption,
            "attached_media": json.dumps([{"media_fbid": photo_id}]),
            "access_token": token,
        },
    )
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"Đăng với ảnh local thất bại: {data}")
    return data["id"]


def fb_post_carousel(token, caption, slide_urls, dry_run=False):
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
        data={"message": caption,
              "attached_media": json.dumps(attached),
              "access_token": token},
    )
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"Đăng carousel thất bại: {data}")
    return data["id"]


def fb_post_text_only(token, caption, dry_run=False):
    """Đăng text-only khi không có ảnh (giỏ hàng chưa có cover_url)."""
    if dry_run:
        return "dry-run-text"
    r = requests.post(
        "https://graph.facebook.com/v19.0/me/feed",
        data={"message": caption, "access_token": token},
    )
    data = r.json()
    if "id" not in data:
        raise RuntimeError(f"Đăng text thất bại: {data}")
    return data["id"]


# ── Airtable update ───────────────────────────────────────────────────────────

def update_iqi_record(at_key, at_base, rec_id, fb_url, slot_time):
    now = datetime.utcnow() + timedelta(hours=7)
    requests.patch(
        f"https://api.airtable.com/v0/{at_base}/{IQI_TABLE}/{rec_id}",
        headers={"Authorization": f"Bearer {at_key}",
                 "Content-Type": "application/json"},
        json={"fields": {
            "Trạng Thái": "Đã đăng",
            "Ngày Đăng":  now.strftime("%Y-%m-%d"),
            "Link FB":    fb_url,
            "Ghi Chú":    f"IQI auto [{slot_time}] {now.strftime('%d/%m/%Y %H:%M')}",
        }},
    )


# ── Telegram ──────────────────────────────────────────────────────────────────

def tg(env, text):
    token   = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_CHAT_ID", "")
    if token and chat_id:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env      = load_env()
    fb_token = env.get("FACEBOOK_TOKEN_BINH_PHAN_IQI", "")
    at_key   = env.get("AIRTABLE_API_KEY", "")
    at_base  = env.get("AIRTABLE_BASE_ID", "")

    if not fb_token:
        print("❌ FACEBOOK_TOKEN_BINH_PHAN_IQI không tìm thấy")
        return

    # Jitter 0–400s trước khi check slot
    if not args.dry_run:
        delay = random.randint(0, 400)
        print(f"⏱  Jitter: {delay}s", flush=True)
        time.sleep(delay)

    now_vn = datetime.utcnow() + timedelta(hours=7)
    today  = now_vn.date()
    ctx    = get_today_context(today)

    print(f"\n🏠 IQI Auto-Post — {now_vn.strftime('%d/%m/%Y %H:%M')} (VN)")
    print(f"   📦 Loại căn: {ctx['unit_type']}  |  🔄 P3/P4: {ctx['p3p4_a']} / {ctx['p3p4_b']}")
    if args.dry_run:
        print("   ⚠️  DRY RUN\n")

    due = get_due_slots(now_vn)
    if not due:
        print("✓ Không có slot nào trong window.")
        return

    print(f"📋 {len(due)} slot:")
    for st, stype in due:
        print(f"   [{st}] {stype}")

    for slot_time, slot_type in due:
        meta    = slot_meta(slot_type, ctx)
        project = meta["project"]
        content = meta["content"]
        unit    = meta["unit_type"]
        is_cta  = meta["is_cta"]

        tag = (" [CTA]" if is_cta else "") + (f" — {unit}" if unit else "")
        print(f"\n{'📌' if is_cta else '📝'} [{slot_time}] {project} | {content}{tag}")

        # ── Giỏ hàng: lấy từ GH table ──
        if content == "gio_hang":
            records = fetch_gio_hang(at_key, at_base, project, unit)
            if not records:
                msg = f"⚠️ GH {project} không có căn {unit} Còn hàng — bỏ slot [{slot_time}]"
                print(f"   {msg}")
                tg(env, f"⚠️ *IQI*: {msg}")
                continue

            caption    = build_gio_hang_caption(project, unit, records,
                                               GH_CONFIG[project])
            cover_path = get_cover_path(project, unit)

            print(f"   ✓ {len(records)} căn {unit} Còn hàng")
            if cover_path:
                print(f"   🖼  Ảnh: {Path(cover_path).name}")
            else:
                print(f"   📝 Text-only (chưa có ảnh cover)")
            if args.dry_run:
                print(f"   [DRY RUN] Caption:\n{caption[:200]}...")
                continue

            try:
                if cover_path:
                    post_id = fb_post_with_local_image(fb_token, caption, cover_path)
                else:
                    post_id = fb_post_text_only(fb_token, caption)
                fb_url = f"https://facebook.com/{post_id}"
                print(f"   ✅ {fb_url}")
                tg(env, f"✅ *IQI GH* [{slot_time}] [{project} {unit}]({fb_url})")
            except Exception as e:
                print(f"   ❌ {e}")
                tg(env, f"❌ *IQI GH lỗi* [{slot_time}] {project}\n`{e}`")
            continue

        # ── Dự án: lấy từ IQI Posts ──
        post = find_du_an_post(at_key, at_base, project, prefer_cta=is_cta)
        if not post:
            msg = f"⚠️ Không có bài Sẵn sàng — {project} [{slot_time}]"
            print(f"   {msg}")
            tg(env, f"⚠️ *IQI Posts cạn bài*\n{project} — cần tạo thêm content!")
            continue

        fields     = post["fields"]
        caption    = fields.get("Caption") or fields.get("Tiêu Đề / Hook", "")
        fmt        = fields.get("Format", "Ảnh đơn")
        slide_urls = json.loads(fields.get("Slide URLs") or "[]")

        print(f"   ✓ {caption[:60]}...")
        if not slide_urls:
            print("   ⚠️  Không có Slide URLs — bỏ qua")
            continue

        if args.dry_run:
            print(f"   [DRY RUN] {fmt} | {len(slide_urls)} ảnh")
            continue

        is_carousel = len(slide_urls) > 1 or "carousel" in fmt.lower()
        try:
            if is_carousel:
                post_id = fb_post_carousel(fb_token, caption, slide_urls)
            else:
                post_id = fb_post_single(fb_token, caption, slide_urls[0])
            fb_url = f"https://facebook.com/{post_id}"
            print(f"   ✅ {fb_url}")
            update_iqi_record(at_key, at_base, post["id"], fb_url, slot_time)
            tg(env, f"✅ *IQI* [{slot_time}] [{project}]({fb_url})")
        except Exception as e:
            print(f"   ❌ {e}")
            tg(env, f"❌ *IQI lỗi* [{slot_time}] {project}\n`{e}`")


if __name__ == "__main__":
    main()
