#!/usr/bin/env python3
"""
Generate Instagram/TikTok carousel PDF — premium portrait photo style.

Style: Portrait photo of Bình (face visible upper half) + gradient overlay
(transparent top → dark bottom). Large lime number + ALL CAPS label + white
heading in the middle zone. Dense body text full-width below.
Matches reference: reference/carousel-ref/q1.jpg – q6.jpg

Usage:
    python3 scripts/generate-carousel.py \
        --json posts/NNN-slug/content.json \
        --output posts/NNN-slug/carousel.pdf \
        --photo context/images/IMG_7928.jpg

Highlight syntax: wrap with **word** for lime accent inline.
Bullet syntax: lines starting with "• " get bullet indentation.

Dimensions: 1080×1350 px (4:5 — Instagram/TikTok standard)
"""

import json, os, re, argparse, glob
from PIL import Image, ImageDraw, ImageFont

# ─────────────────────────────────────────────
# BRAND
# ─────────────────────────────────────────────
BRAND_LOGO   = "BìnhPhan IQI"                # top-right logo mark
BRAND_FULL   = "Bình Phan  |  IQI Đà Nẵng"
AUTHOR_NAME  = "Bình Phan"
AUTHOR_ROLE  = "IQI Đà Nẵng  ·  0905 436 789"

# ─────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────
LIME          = (200, 230, 74)    # #C8E64A — number accent, dots
WHITE         = (255, 255, 255)
OFF_WHITE     = (240, 240, 240)   # body text
DIM_WHITE     = (210, 210, 210)   # secondary body
GRAY          = (160, 160, 160)   # brand full tag
HEADING_COLOR = (245, 160, 80)    # pastel orange — headings, highlights, takeaway

W, H = 1080, 1620   # 2:3 ratio — matches q1-q6 reference proportions

# Text zone: 5/7 of canvas width, centered horizontally
TEXT_W = W * 5 // 7        # 771 px
TEXT_X = (W - TEXT_W) // 2  # 154 px — left edge

# ─────────────────────────────────────────────
# FONTS — Be Vietnam Pro
# ─────────────────────────────────────────────
_FD  = os.path.expanduser("~/Library/Fonts")
_SS  = "/System/Library/Fonts/Supplemental"
_SF  = "/System/Library/Fonts"

def _fp(*names):
    for n in names:
        for d in [_FD, _SS, _SF]:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None

_BOLD     = _fp("BeVietnamPro-Bold.ttf")
_SEMIBOLD = _fp("BeVietnamPro-SemiBold.ttf")
_MEDIUM   = _fp("BeVietnamPro-Medium.ttf")
_REGULAR  = _fp("BeVietnamPro-Regular.ttf")
_ITALIC   = _fp("BeVietnamPro-Italic.ttf")
_LIGHT    = _fp("BeVietnamPro-Light.ttf")

_FB_BOLD = _fp("Arial Bold.ttf","arialbd.ttf")
_FB_REG  = _fp("Arial Unicode.ttf","arial.ttf","Arial.ttf")
_FB_ITAL = _fp("Arial Italic.ttf","ariali.ttf")


def _load(sz, *paths):
    for p in paths:
        if p and os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except OSError: pass
    return ImageFont.load_default()

def font_bold(sz):      return _load(sz, _BOLD,     _FB_BOLD, _FB_REG)
def font_semibold(sz):  return _load(sz, _SEMIBOLD,  _BOLD,    _FB_BOLD)
def font_medium(sz):    return _load(sz, _MEDIUM,    _REGULAR, _FB_REG)
def font_regular(sz):   return _load(sz, _REGULAR,   _FB_REG)
def font_italic(sz):    return _load(sz, _ITALIC,    _FB_ITAL, _FB_REG)
def font_light(sz):     return _load(sz, _LIGHT,     _REGULAR, _FB_REG)
def font_bolditalic(sz): return _load(sz, _ITALIC,   _FB_ITAL, _FB_REG)  # italic fallback


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _tw(t, f):
    b = f.getbbox(t); return b[2]-b[0]

def _th(t, f):
    b = f.getbbox(t); return b[3]-b[1]

def _lh(f, mul=1.22):
    return int(_th("Agj", f) * mul)


_NUM_RE = re.compile(r'(\d[\d.,/%+]*)')   # standalone numeric token

# Cover title: "số + keyword" compounds rendered WHITE (base = HEADING_COLOR)
_COVER_COMPOUND_RE = re.compile(
    r'\d[\d.,]*\s+(?:điều|lý do|bí mật|nguyên tắc|con số|năm|ví dụ|bước|lần|cách|quyết định|câu hỏi|nguyên lý)',
    re.IGNORECASE | re.UNICODE
)

# Compound number+unit expressions to highlight as a whole phrase
_COMPOUND_RE = re.compile(
    r'tầng\s+\d[\d\-]*'                                          # tầng 5, tầng 7-10
    r'|\d[\d.,]*(?:[-–]\d[\d.,]*)?(?:m²|m2|km²|km|%|ha)'        # 20m2, 2km, 59% (no space)
    r'|\d[\d.,]*(?:[-–]\d[\d.,]*)?\s+'
      r'(?:triệu|tỷ|năm|tháng|ngày|tuần|điều|ví dụ|lần|căn|tòa|tháp|phòng|block)',
    re.IGNORECASE | re.UNICODE
)


def wrap_text(text, font, max_w):
    """Plain word-wrap. Returns list of line strings."""
    words = text.split()
    lines, cur, cw = [], "", 0
    sp = _tw(" ", font)
    for w in words:
        ww = _tw(w, font)
        gap = sp if cur else 0
        if cw + gap + ww <= max_w or not cur:
            cur = f"{cur} {w}".strip(); cw += gap + ww
        else:
            lines.append(cur); cur, cw = w, ww
    if cur: lines.append(cur)
    return lines


def _word_width(word, f_base, f_hi):
    """Measure a word accounting for mixed fonts in highlighted tokens."""
    if f_hi is f_base:
        return _tw(word, f_base)
    total = 0
    for tok in _NUM_RE.split(word):
        if not tok: continue
        total += _tw(tok, f_hi if _NUM_RE.fullmatch(tok) else f_base)
    return total


def draw_rich(draw, text, font, x, y, max_w,
              color=OFF_WHITE, hi=LIME, bullet_indent=28, mul=1.22,
              font_hi=None, auto_hi_nums=False):
    """
    Render text with:
      **word**  → hi color + font_hi
      • lines   → bullet with indent
      auto_hi_nums=True → numeric tokens auto-highlighted
    Returns y after last line.
    """
    if font_hi is None:
        font_hi = font
    lh = _lh(font, mul)
    sp = _tw(" ", font)
    raw_lines = text.split("\n")

    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            y += lh // 2
            continue

        is_bullet = raw.startswith("• ") or raw.startswith("•")
        if is_bullet:
            raw = raw.lstrip("•").strip()
            dot_r = 4
            dot_y = y + lh // 2 - dot_r
            draw.ellipse([(x, dot_y), (x + dot_r*2, dot_y + dot_r*2)], fill=color)
            line_x, line_max = x + bullet_indent, max_w - bullet_indent
        else:
            line_x, line_max = x, max_w

        # Parse **highlight** + compound/standalone number detection
        parts = []
        for seg in re.split(r'(\*\*[^*]+\*\*)', raw):
            if seg.startswith('**') and seg.endswith('**'):
                for w in seg[2:-2].split(): parts.append((w, True))
            else:
                # Wrap compound expressions first, then re-split
                if auto_hi_nums:
                    seg = _COMPOUND_RE.sub(r'**\g<0>**', seg)
                for subseg in re.split(r'(\*\*[^*]+\*\*)', seg):
                    if subseg.startswith('**') and subseg.endswith('**'):
                        for w in subseg[2:-2].split(): parts.append((w, True))
                    else:
                        for w in subseg.split():
                            is_num = auto_hi_nums and bool(_NUM_RE.fullmatch(w))
                            parts.append((w, is_num))

        # Word-wrap using per-token font width
        lines_out, cur_line, cw = [], [], 0
        for word, is_hi in parts:
            ww = _tw(word, font_hi if is_hi else font)
            gap = sp if cur_line else 0
            if cw + gap + ww <= line_max or not cur_line:
                cur_line.append((word, is_hi)); cw += gap + ww
            else:
                lines_out.append(cur_line)
                cur_line, cw = [(word, is_hi)], ww
        if cur_line: lines_out.append(cur_line)

        for line_parts in lines_out:
            cx = line_x
            for i, (word, is_hi) in enumerate(line_parts):
                if i > 0:
                    draw.text((cx, y), " ", font=font, fill=color)
                    cx += sp
                f = font_hi if is_hi else font
                draw.text((cx, y), word, font=f, fill=(hi if is_hi else color))
                cx += _tw(word, f)
            y += lh

    return y


# ── Heading with inline numbers at 60pt white ─────────────────────────────

def wrap_heading_mixed(text, f_base, max_w, num_pt=70):
    """Word-wrap heading, measuring numeric tokens at num_pt bold."""
    f_num = font_bold(num_pt)
    sp = _tw(" ", f_base)
    words, lines, cur, cw = text.split(), [], "", 0
    for word in words:
        ww = sum(
            _tw(t, f_num if _NUM_RE.fullmatch(t) else f_base)
            for t in _NUM_RE.split(word) if t
        )
        gap = sp if cur else 0
        if cw + gap + ww <= max_w or not cur:
            cur = (cur + " " + word).strip(); cw += gap + ww
        else:
            lines.append(cur); cur, cw = word, ww
    if cur: lines.append(cur)
    return lines


def draw_heading_line_mixed(draw, line, f_base, x, y, num_pt=70):
    """Render one heading line: text in HEADING_COLOR, numeric tokens WHITE at num_pt."""
    f_num = font_bold(num_pt)
    sp    = _tw(" ", f_base)
    bh    = _th("H", f_base)
    cx    = x
    for i, word in enumerate(line.split()):
        if i > 0:
            draw.text((cx, y), " ", font=f_base, fill=HEADING_COLOR)
            cx += sp
        for tok in _NUM_RE.split(word):
            if not tok: continue
            if _NUM_RE.fullmatch(tok):
                th = _th(tok, f_num)
                dy = max(0, (th - bh) // 2)
                draw.text((cx + 1, y - dy + 1), tok, font=f_num, fill=(0,0,0,80))
                draw.text((cx, y - dy), tok, font=f_num, fill=WHITE)
                cx += _tw(tok, f_num)
            else:
                draw.text((cx, y), tok, font=f_base, fill=HEADING_COLOR)
                cx += _tw(tok, f_base)


# ─────────────────────────────────────────────
# BACKGROUND + OVERLAY
# ─────────────────────────────────────────────

def load_and_crop(photo_path):
    """Fill-crop to W×H, top-biased to keep face in upper portion."""
    img = Image.open(photo_path).convert("RGB")
    iw, ih = img.size
    ratio = max(W / iw, H / ih)
    nw, nh = int(iw * ratio), int(ih * ratio)
    img = img.resize((nw, nh), Image.LANCZOS)
    ox = (nw - W) // 2
    # Top-biased: use 15% from top (not 50%) so face stays visible
    oy = max(0, int((nh - H) * 0.15))
    return img.crop((ox, oy, ox + W, oy + H))


OVERLAY_ALPHA = 140  # 55% uniform black overlay across full photo


def make_bg(photo_path=None):
    """Photo + uniform 55% black overlay, or solid dark fallback."""
    if photo_path and os.path.exists(photo_path):
        base = load_and_crop(photo_path).convert("RGBA")
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, OVERLAY_ALPHA))
        return Image.alpha_composite(base, overlay).convert("RGB")
    return Image.new("RGB", (W, H), (15, 15, 15))


# ─────────────────────────────────────────────
# BRAND ELEMENTS
# ─────────────────────────────────────────────

def draw_brand_logo(draw):
    """'BìnhPhan ' in WHITE, 'IQI' in HEADING_COLOR."""
    f       = font_semibold(26)
    prefix  = "BìnhPhan "
    suffix  = "IQI"
    total_w = _tw(BRAND_LOGO, f)
    x = W - total_w - 48
    y = 36
    draw.text((x + 1, y + 1), BRAND_LOGO, font=f, fill=(0, 0, 0, 100))
    draw.text((x, y), prefix, font=f, fill=WHITE)
    draw.text((x + _tw(prefix, f), y), suffix, font=f, fill=HEADING_COLOR)


def draw_num_dot(draw, cx, y, r=7):
    """Decorative lime dot — below number."""
    draw.ellipse([(cx - r, y), (cx + r, y + r*2)], fill=LIME)


def draw_separator_dot(draw, x, y, r=5):
    """White separator dot between heading and body."""
    draw.ellipse([(x, y), (x + r*2, y + r*2)], fill=WHITE)


# ─────────────────────────────────────────────
# NUMBER DISPLAY — strip leading zero
# ─────────────────────────────────────────────

def display_num(raw):
    """'01' → '1', '10' → '10', 'A' → 'A'."""
    s = str(raw).strip()
    if s.isdigit():
        return str(int(s))   # removes leading zero
    return s


# ─────────────────────────────────────────────
# SLIDE GENERATORS
# ─────────────────────────────────────────────

NUM_Y    = 740      # y where text zone starts — below face zone
BODY_GAP = 24


def make_cover_slide(title, subtitle="", photo_path=None):
    img = make_bg(photo_path)
    draw = ImageDraw.Draw(img)
    draw_brand_logo(draw)

    # Accent bar — HEADING_COLOR
    draw.rectangle([(TEXT_X, NUM_Y - 36), (TEXT_X + 80, NUM_Y - 31)], fill=HEADING_COLOR)

    # Title — ALL CAPS, 68pt, HEADING_COLOR; "số + keyword" compounds → WHITE
    f_title = font_bold(68)
    y = NUM_Y
    title_marked = _COVER_COMPOUND_RE.sub(r'**\g<0>**', title)
    title_final  = title_marked.upper()
    y = draw_rich(draw, title_final, f_title, TEXT_X, y, TEXT_W,
                  color=HEADING_COLOR, hi=WHITE, font_hi=f_title,
                  mul=1.35)

    # Rule — HEADING_COLOR
    y += 18
    draw.rectangle([(TEXT_X, y), (TEXT_X + 96, y + 4)], fill=HEADING_COLOR)
    y += 26

    if subtitle:
        f_sub    = font_regular(33)     # 26pt × 1.25 = 32.5 → 33pt
        f_sub_hi = font_bolditalic(33)
        y = draw_rich(draw, subtitle, f_sub, TEXT_X, y, TEXT_W,
                      color=OFF_WHITE, hi=HEADING_COLOR,
                      font_hi=f_sub_hi, auto_hi_nums=True,
                      mul=1.90)

    f_hint = font_light(22)
    draw.text((TEXT_X, H - 90), "vuốt để xem  →", font=f_hint, fill=GRAY)
    return img


def make_content_slide(number, heading, subtitle, takeaway,
                       label="", photo_path=None):
    img = make_bg(photo_path)
    draw = ImageDraw.Draw(img)
    draw_brand_logo(draw)

    num_str       = display_num(number)           # e.g. "1", "2"
    HEAD_PT       = 58
    f_head        = font_bold(HEAD_PT)
    lh_head       = _lh(f_head, 1.35)
    heading_upper = heading.upper()

    # ── PASS 1: estimate heading lines (use 90% width) ──────────────────────
    est_text_maxw = int(TEXT_W * 0.90)
    h_lines_est   = wrap_text(heading_upper, f_head, est_text_maxw)
    n_head_lines  = len(h_lines_est)

    # Number size: 265pt for 3+ lines, 165pt for 1-2 lines
    num_pt = 265 if n_head_lines >= 3 else 165
    f_num  = font_bold(num_pt)
    nw     = _tw(num_str, f_num)
    nh     = _th(num_str, f_num)

    # ── PASS 2: real column widths ───────────────────────────
    nx        = TEXT_X
    text_x    = nx + nw + 20
    text_maxw = (TEXT_X + TEXT_W) - text_x
    h_lines   = wrap_text(heading_upper, f_head, text_maxw)
    while len(h_lines) > 4 and HEAD_PT > 38:
        HEAD_PT -= 2
        f_head  = font_bold(HEAD_PT)
        lh_head = _lh(f_head, 1.35)
        h_lines = wrap_text(heading_upper, f_head, text_maxw)

    # ── HEADING BLOCK HEIGHT → used for bottom-alignment ────
    f_label    = font_semibold(22)
    lh_label   = _lh(f_label, 1.2)
    label_text = (label or "").upper().strip()
    label_h    = (lh_label + 6) if label_text else 0
    head_block_h = label_h + len(h_lines) * lh_head

    # Shift text zone down 13px when heading spans 3 lines
    zone_y = NUM_Y + (30 if len(h_lines) >= 3 else 0)

    # Bottom of number == bottom of (last-1) heading line, shifted down 13px
    lines_before_last = max(1, len(h_lines) - 1)
    num_bottom_y = zone_y + label_h + lines_before_last * lh_head + 13
    num_draw_y   = num_bottom_y - nh
    ty_end       = zone_y + head_block_h   # full heading block bottom (for body start)

    # ── LARGE NUMBER — WHITE, multi-layer shadow ─────────────
    for sx, sy, sa in [(10, 10, 30), (6, 6, 55), (3, 3, 85), (1, 1, 110)]:
        draw.text((nx + sx, num_draw_y + sy), num_str, font=f_num, fill=(0,0,0,sa))
    draw.text((nx, num_draw_y), num_str, font=f_num, fill=WHITE)

    # ── LABEL + HEADING (start from zone_y top) ─────────────
    ty = zone_y
    if label_text:
        draw.text((text_x, ty), label_text, font=f_label, fill=HEADING_COLOR)
        ty += lh_label + 6

    for line in h_lines:
        draw.text((text_x + 1, ty + 1), line, font=f_head, fill=(0, 0, 0, 80))
        draw.text((text_x, ty), line, font=f_head, fill=HEADING_COLOR)
        ty += lh_head

    # ── BODY TEXT ────────────────────────────────────────────
    BODY_SPACING = 45
    body_y = ty_end + BODY_SPACING

    f_body    = font_regular(30)
    f_body_hi = font_bolditalic(30)

    full_body = subtitle or ""
    if takeaway:
        full_body = (full_body + "\n\n" + takeaway).strip() if full_body else takeaway

    if full_body:
        draw_rich(draw, full_body, f_body,
                  TEXT_X, body_y, TEXT_W,
                  color=WHITE, hi=HEADING_COLOR,
                  font_hi=f_body_hi, auto_hi_nums=True,
                  mul=1.90)
    return img


def make_cta_slide(heading, subtitle="", photo_path=None):
    img = make_bg(photo_path)
    draw = ImageDraw.Draw(img)
    draw_brand_logo(draw)

    mid_x = TEXT_X + TEXT_W // 2

    # Heading — ALL CAPS, HEADING_COLOR, centered in text zone
    f_head  = font_bold(62)
    lh_head = _lh(f_head, 1.35)
    h_lines = wrap_text(heading.upper(), f_head, TEXT_W)
    y = NUM_Y
    for line in h_lines:
        cx = TEXT_X + (TEXT_W - _tw(line, f_head)) // 2
        draw.text((cx + 2, y + 2), line, font=f_head, fill=(0,0,0,100))
        draw.text((cx, y), line, font=f_head, fill=HEADING_COLOR)
        y += lh_head

    # Rule — HEADING_COLOR
    y += 14
    draw.rectangle([(mid_x - 44, y), (mid_x + 44, y + 3)], fill=HEADING_COLOR)
    y += 22

    if subtitle:
        f_sub = font_regular(25)
        sub_lines = wrap_text(subtitle, f_sub, TEXT_W)
        for line in sub_lines:
            cx = TEXT_X + (TEXT_W - _tw(line, f_sub)) // 2
            draw.text((cx, y), line, font=f_sub, fill=OFF_WHITE)
            y += _lh(f_sub, 1.38)

    # Author block
    y = max(y + 40, H - 320)
    draw.line([(mid_x - 90, y), (mid_x + 90, y)], fill=(100,100,100), width=1)
    y += 28

    f_name = font_semibold(32)
    cx = TEXT_X + (TEXT_W - _tw(AUTHOR_NAME, f_name)) // 2
    draw.text((cx, y), AUTHOR_NAME, font=f_name, fill=WHITE)
    y += _lh(f_name, 1.3)

    f_role = font_light(22)
    cx = TEXT_X + (TEXT_W - _tw(AUTHOR_ROLE, f_role)) // 2
    draw.text((cx, y), AUTHOR_ROLE, font=f_role, fill=GRAY)
    y += _lh(f_role, 1.3)

    # 3 dots — HEADING_COLOR
    y += 14
    for i in range(3):
        cdx = mid_x + (i - 1) * 26
        draw.ellipse([(cdx-5, y-5), (cdx+5, y+5)], fill=HEADING_COLOR)

    return img


# ─────────────────────────────────────────────
# PHOTO COLLECTION
# ─────────────────────────────────────────────

def collect_photos(photo_arg, photos_dir_arg):
    if photo_arg and os.path.exists(photo_arg):
        return [photo_arg]
    if photos_dir_arg and os.path.isdir(photos_dir_arg):
        files = []
        for ext in ("*.jpg","*.JPG","*.jpeg","*.JPEG","*.png","*.PNG",
                    "*.webp","*.WEBP"):
            files.extend(glob.glob(os.path.join(photos_dir_arg, ext)))
        files = sorted(set(files))
        if files:
            return files
    return [None]


# ─────────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────────

def generate_carousel(content, output_path, photos):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    all_slides = content.get("slides", [])

    # Separate by role
    content_slides = [s for s in all_slides
                      if str(s.get("number","")).strip() not in ("", "00")]
    cta_data = next(
        (s for s in reversed(all_slides)
         if str(s.get("number","")).strip() == ""),
        None
    )
    cover_00 = next(
        (s for s in all_slides if str(s.get("number","")).strip() == "00"),
        None
    )

    n_total = len(content_slides) + 2

    def photo_for(i):
        if not photos or photos[0] is None: return None
        return photos[i % len(photos)]

    slides = []

    # ── COVER ────────────────────────────────────────────
    cover_sub = content.get("subtitle", "")
    if not cover_sub and cover_00:
        cover_sub = cover_00.get("subtitle", "")
    slides.append(make_cover_slide(content["title"], cover_sub, photo_for(0)))

    # ── CONTENT SLIDES ───────────────────────────────────
    for i, sd in enumerate(content_slides):
        slides.append(make_content_slide(
            number   = sd.get("number", i + 1),
            heading  = sd.get("heading", ""),
            subtitle = sd.get("subtitle", ""),
            takeaway = sd.get("takeaway", ""),
            label    = sd.get("label", ""),
            photo_path = photo_for(i + 1),
        ))

    # ── CTA ──────────────────────────────────────────────
    if cta_data:
        cta_heading = cta_data.get("heading", "Lưu bài này lại.")
        cta_sub     = cta_data.get("subtitle", "") or cta_data.get("takeaway", "")
    else:
        cta_heading = content.get("cta_text", "Lưu bài này lại.")
        cta_sub     = content.get("cta_subtitle", "")
    slides.append(make_cta_slide(cta_heading, cta_sub, photo_for(n_total - 1)))

    # ── SAVE PDF ─────────────────────────────────────────
    slides[0].save(
        output_path, "PDF",
        resolution=100.0,
        save_all=True,
        append_images=slides[1:],
    )
    print(f"✓  Carousel → {output_path}  ({len(slides)} slides)")

    # ── SAVE SLIDE PNGs ──────────────────────────────────
    png_dir = os.path.splitext(output_path)[0] + "-slides"
    os.makedirs(png_dir, exist_ok=True)
    for i, slide in enumerate(slides):
        slide.save(os.path.join(png_dir, f"slide-{i:02d}.png"))
    print(f"✓  PNGs    → {png_dir}/")

    return output_path


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────
DEMO = {
    "title":    "10 Năm — 4 Quyết Định Thay Đổi Hành Trình",
    "subtitle": "Không phải lúc nào cũng đúng. Nhưng mỗi lần đều học được thứ gì đó thật.",
    "slides": [
        { "number": "00",
          "heading": "10 Năm — 4 Quyết Định",
          "subtitle": "Không phải lúc nào cũng đúng.",
          "takeaway": "Bình Phan — 10 năm BĐS" },
        { "number": "01",
          "label": "Bài học đầu tiên",
          "heading": "3 ngày đầu — 4 lô đất",
          "subtitle": "Ngày đầu vào nghề. Mình không biết mình đang làm gì.\n\n• Bán được **4 lô** trong **3 ngày**. Lúc đó tưởng mình có năng khiếu.\n• Mãi sau mới hiểu: đó là **thị trường tốt**, không phải mình giỏi.",
          "takeaway": "Phân biệt được 2 điều này mất khá nhiều năm." },
        { "number": "02",
          "label": "Thoát đỉnh 2019",
          "heading": "Chốt hết, ra ngoài",
          "subtitle": "Thị trường quá dễ — ai cũng đang vui. **Mình sợ.**\n\n• Bán hết danh mục **tháng 3/2019**.\n• 6 tháng sau thị trường đảo chiều.",
          "takeaway": "Không phải mình nhìn ra gì đặc biệt — chỉ để ý thấy người mua thật đang ít dần." },
        { "number": "",
          "heading": "Mình vẫn đang học",
          "subtitle": "10 năm không làm mình biết tất cả.",
          "takeaway": "" },
    ],
}


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Premium portrait carousel generator (q1-q6 style)")
    p.add_argument("--json",   help="JSON content file")
    p.add_argument("--output", default="outputs/carousel-test.pdf")
    p.add_argument("--photo",  help="Single portrait photo for all slides")
    p.add_argument("--photos", help="Directory of photos to cycle")
    args = p.parse_args()

    content = DEMO
    if args.json:
        with open(args.json, encoding="utf-8") as f:
            content = json.load(f)

    photos = collect_photos(args.photo, args.photos)
    generate_carousel(content, args.output, photos)
