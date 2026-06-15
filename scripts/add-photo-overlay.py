#!/usr/bin/env python3
"""
Add luxury text overlay to personal photos for social media posts.

Usage:
    python3 scripts/add-photo-overlay.py \
        --photo context/images/chan-dung-vest-navy-khoanh-tay.jpg \
        --text "10 năm đất nền — tại sao mình chủ động rời đi" \
        --highlight "CHỦ ĐỘNG" \
        --eyebrow "Góc nhìn nghề" \
        --output posts/010-roi-dat-nen/image.png

    # Non-person photo (landscape / property):
    python3 scripts/add-photo-overlay.py \
        --photo context/images/bai-bien-hoang-hon-phan-chieu.jpg \
        --text "Đà Nẵng Q1 2026 — thị trường đang nói gì" \
        --no-person \
        --output posts/NNN/image.png

Rules:
  - Main hook text: uppercased, BeVietnamPro-Bold (sans-serif), pastel yellow
  - --highlight words rendered WHITE with shadow
  - --eyebrow (optional): serif eyebrow line above hook, Cormorant Garamond Light,
    white, sentence case, small letter-spacing feel
  - Gradient: linear 0%→75% from H/2 to bottom
  - Brand mark: top-right, "BìnhPhan" white + "IQI" pastel yellow
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
TEXT_COLOR      = (255, 220, 80)    # Pastel yellow
HIGHLIGHT_COLOR = (255, 255, 255)   # White for highlighted words
BLACK           = (0, 0, 0)
WHITE           = (255, 255, 255)
EYEBROW_COLOR   = (255, 255, 255, 200)  # White, slight transparency

W, H = 1080, 1350

FONT_DIR         = "/Users/macos/Library/Fonts"
FONT_MEDIUM      = f"{FONT_DIR}/BeVietnamPro-Medium.ttf"
FONT_BOLD        = f"{FONT_DIR}/BeVietnamPro-Bold.ttf"
FONT_SERIF_LIGHT = f"{FONT_DIR}/CormorantGaramond-Light.ttf"


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def draw_lines(draw, lines, cx, y, font_med, font_semi, hi_set, lh):
    """Draw hook lines centered at cx.
    All words Bold. Highlight = white, regular = pastel yellow. No shadows."""
    for line in lines:
        lw = draw.textbbox((0, 0), line, font=font_med)[2]
        words = line.split(" ")
        x = cx - lw // 2
        for i, word in enumerate(words):
            is_hi  = word in hi_set
            font   = font_med  # both bold now
            color  = HIGHLIGHT_COLOR if is_hi else TEXT_COLOR
            suffix = " " if i < len(words) - 1 else ""
            draw.text((x, y), word, font=font, fill=color)
            x += draw.textbbox((0, 0), word + suffix, font=font)[2]
        y += lh
    return y


def draw_eyebrow(draw, text, cx, y, font):
    """Draw serif eyebrow line — centered, white with soft shadow."""
    tw = draw.textbbox((0, 0), text, font=font)[2]
    x  = cx - tw // 2
    draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0, 80))
    draw.text((x, y), text, font=font, fill=WHITE)
    # thin decorative rule below eyebrow
    rule_w = min(tw + 40, 320)
    rule_x = cx - rule_w // 2
    rule_y = y + draw.textbbox((0, 0), text, font=font)[3] + 8
    draw.line([(rule_x, rule_y), (rule_x + rule_w, rule_y)],
              fill=(255, 255, 255, 120), width=1)


def add_overlay(photo_path, hook_text, output_path,
                highlight_words=None, eyebrow=None,
                position="bottom", no_person=False):

    # Load & cover-crop to 1080×1350
    img = Image.open(photo_path).convert("RGBA")
    ow, oh = img.size
    scale  = max(W / ow, H / oh)
    img    = img.resize((int(ow * scale), int(oh * scale)), Image.LANCZOS)
    nw, nh = img.size
    img    = img.crop(((nw - W) // 2, (nh - H) // 2,
                       (nw - W) // 2 + W, (nh - H) // 2 + H))

    # ── Gradient overlay ────────────────────────────────
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dv = ImageDraw.Draw(ov)

    if no_person:
        # Smooth fade: 0% at H*0.45 → 70% at bottom
        fade_s    = int(H * 0.45)
        max_alpha = int(255 * 0.70)
        for y in range(fade_s, H):
            t = (y - fade_s) / (H - fade_s)
            dv.line([(0, y), (W, y)], fill=(0, 0, 0, int(max_alpha * t)))
    else:
        flat_alpha = int(255 * 0.60)
        if position == "bottom":
            fade_s    = H // 2
            max_alpha = int(255 * 0.75)
            for y in range(fade_s, H):
                t = (y - fade_s) / (H - fade_s)
                dv.line([(0, y), (W, y)], fill=(0, 0, 0, int(max_alpha * t)))
        elif position == "top":
            fade_s, fade_e = int(H * 1 / 3), H // 2
            for y in range(0, fade_s):
                dv.line([(0, y), (W, y)], fill=(0, 0, 0, flat_alpha))
            for y in range(fade_s, fade_e):
                t = 1 - (y - fade_s) / (fade_e - fade_s)
                dv.line([(0, y), (W, y)], fill=(0, 0, 0, int(flat_alpha * t)))
        else:  # center
            y1, y2 = int(H * 0.35), int(H * 0.70)
            mid, half = (y1 + y2) / 2, (y2 - y1) / 2
            for y in range(y1, y2):
                t = 1 - abs(y - mid) / half
                dv.line([(0, y), (W, y)], fill=(0, 0, 0, int(flat_alpha * t)))

    img  = Image.alpha_composite(img, ov)
    draw = ImageDraw.Draw(img)

    # ── Fonts ────────────────────────────────────────────
    font_med    = load_font(FONT_BOLD, 38)   # bold for all text
    font_bold   = load_font(FONT_BOLD, 38)
    font_serif  = load_font(FONT_SERIF_LIGHT, 26)

    max_w    = W - 160 * 2   # 760px
    lh       = 38 + 16
    hook_upper = hook_text.upper()
    lines    = wrap_text(hook_upper, font_med, max_w, draw)
    total_h  = len(lines) * lh

    # eyebrow height (serif line + rule + gap below)
    eyebrow_block_h = 0
    if eyebrow:
        eb_bbox = draw.textbbox((0, 0), eyebrow, font=font_serif)
        eyebrow_block_h = eb_bbox[3] + 8 + 1 + 18  # text + rule + gap

    # ── Text anchor — constrained to 25%–75% of image height ──
    # H=1350 → safe zone: 337–1012px
    if position == "bottom":
        # anchor text bottom edge near 72% → block_top ~ 60–65%
        block_top = int(H * 0.63) - total_h // 2
        block_top = max(int(H * 0.25), min(block_top, int(H * 0.72) - total_h))
    elif position == "top":
        # anchor text top edge near 27%
        block_top = int(H * 0.27)
        block_top = max(int(H * 0.25), min(block_top, int(H * 0.50) - total_h))
    else:
        block_top = (H - eyebrow_block_h - total_h) // 2
        block_top = max(int(H * 0.25), min(block_top, int(H * 0.75) - total_h))

    # Draw eyebrow serif line first
    if eyebrow:
        draw_eyebrow(draw, eyebrow, W // 2, block_top, font_serif)
        block_top += eyebrow_block_h

    # Build hi_set
    hi_set = set()
    for phrase in (highlight_words or []):
        for w in phrase.upper().split():
            hi_set.add(w)

    draw_lines(draw, lines, W // 2, block_top, font_med, font_bold, hi_set, lh)

    # ── Brand mark: top-right ────────────────────────────
    bf    = load_font(FONT_BOLD, 23)
    part1 = "BìnhPhan "
    part2 = "IQI"
    w1    = draw.textbbox((0, 0), part1, font=bf)[2]
    w2    = draw.textbbox((0, 0), part2, font=bf)[2]
    bx    = W - w1 - w2 - 40
    by    = 36
    draw.text((bx + 1, by + 1), part1, font=bf, fill=(0, 0, 0, 100))
    draw.text((bx + w1 + 1, by + 1), part2, font=bf, fill=(0, 0, 0, 100))
    draw.text((bx, by), part1, font=bf, fill=WHITE)
    draw.text((bx + w1, by), part2, font=bf, fill=TEXT_COLOR)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"Saved: {output_path} ({os.path.getsize(output_path):,} bytes)")


def main():
    p = argparse.ArgumentParser(
        description="Add luxury text overlay to personal photos"
    )
    p.add_argument("--photo",     required=True)
    p.add_argument("--text",      required=True)
    p.add_argument("--output",    required=True)
    p.add_argument("--highlight", nargs="*", default=[])
    p.add_argument("--eyebrow",   default=None,
                   help="Serif eyebrow line above main hook (Cormorant Garamond Light)")
    p.add_argument("--position",  choices=["bottom", "top", "center"],
                   default="bottom")
    p.add_argument("--no-person", action="store_true",
                   help="Non-person photo: flat 50%% at bottom 1/3")
    p.add_argument("--white", action="store_true",
                   help="All-white text (dùng cho ảnh storytelling/đen trắng)")
    args = p.parse_args()

    if args.white:
        global TEXT_COLOR
        TEXT_COLOR = (255, 255, 255)

    if not os.path.exists(args.photo):
        print(f"ERROR: photo not found: {args.photo}", file=sys.stderr)
        sys.exit(1)

    add_overlay(
        photo_path      = args.photo,
        hook_text       = args.text,
        output_path     = args.output,
        highlight_words = args.highlight,
        eyebrow         = args.eyebrow,
        position        = args.position,
        no_person       = args.no_person,
    )


if __name__ == "__main__":
    main()
