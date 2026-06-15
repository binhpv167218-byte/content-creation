#!/usr/bin/env python3
"""Translate Vietnamese text in Symphony 5 floor plan to English."""

from PIL import Image, ImageDraw, ImageFont
import os

IMG_PATH = "/Users/macos/Desktop/content-creation/context/images/projects/sun-symphony/symphony5-mat-bang-tang-3a-18.jpg"
OUT_PATH = "/Users/macos/Desktop/content-creation/context/images/projects/sun-symphony/symphony5-floor-plan-3a-18-en.jpg"

# ------------------------------------------------------------------
# Font helpers
# ------------------------------------------------------------------
def get_font(size, bold=False):
    tries = []
    if bold:
        tries = [
            ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
            ("/System/Library/Fonts/Helvetica.ttc", 1),
            ("/System/Library/Fonts/Supplemental/Arial.ttf", 0),
        ]
    else:
        tries = [
            ("/System/Library/Fonts/Supplemental/Arial.ttf", 0),
            ("/System/Library/Fonts/Helvetica.ttc", 0),
        ]
    for path, idx in tries:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=idx)
            except Exception:
                pass
    return ImageFont.load_default()

def fit_text(draw, rect, text, bold=False, color=(0,0,0), max_size=120, align="center"):
    x1, y1, x2, y2 = rect
    rw, rh = x2-x1, y2-y1
    for size in range(max_size, 8, -2):
        font = get_font(size, bold)
        bb = draw.textbbox((0,0), text, font=font)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]
        if tw <= rw*0.90 and th <= rh*0.85:
            if align == "center":
                cx = x1 + (rw-tw)//2 - bb[0]
                cy = y1 + (rh-th)//2 - bb[1]
            elif align == "left":
                cx = x1 + 6 - bb[0]
                cy = y1 + (rh-th)//2 - bb[1]
            draw.text((cx, cy), text, font=font, fill=color)
            return font, size
    font = get_font(8)
    draw.text((x1+2, y1+2), text, font=font, fill=color)
    return font, 8

# ------------------------------------------------------------------
# Find unit label bounding boxes by scanning for amber header pixels
# ------------------------------------------------------------------
def find_unit_label_boxes(img):
    """Return list of (x1,y1,x2,y2) for each unit label bounding box."""
    W, H = img.size
    # Scan every 3px for speed
    amber_pts = set()
    for y in range(100, H, 3):
        for x in range(200, W-20, 3):
            px = img.getpixel((x, y))
            r, g, b = px[0], px[1], px[2]
            # Amber/golden header: warm tone, not too bright or dark
            if (195 <= r <= 238 and 162 <= g <= 208 and 100 <= b <= 168
                    and r >= b + 38 and r >= g - 20):
                amber_pts.add((x, y))

    print(f"  Found {len(amber_pts)} amber pixels")

    # Cluster into connected regions (simple flood-fill style grouping)
    visited = set()
    boxes = []

    for pt in sorted(amber_pts):
        if pt in visited:
            continue
        # BFS to find connected cluster
        cluster = []
        queue = [pt]
        while queue:
            cx, cy = queue.pop()
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))
            cluster.append((cx, cy))
            for dx in [-3, 0, 3]:
                for dy in [-3, 0, 3]:
                    np_ = (cx+dx, cy+dy)
                    if np_ in amber_pts and np_ not in visited:
                        queue.append(np_)

        if len(cluster) < 20:  # skip noise
            continue

        xs = [p[0] for p in cluster]
        ys = [p[1] for p in cluster]
        bx1, bx2 = min(xs), max(xs)
        by1, by2 = min(ys), max(ys)

        # Filter: a unit label header is narrow in height (< 80px) and reasonably wide
        if (by2 - by1) > 80:
            continue
        if (bx2 - bx1) < 60:
            continue

        boxes.append((bx1, by1, bx2, by2))

    # Merge overlapping/nearby boxes
    boxes.sort()
    merged = []
    for box in boxes:
        if merged:
            px1, py1, px2, py2 = merged[-1]
            bx1, by1, bx2, by2 = box
            # If same y-band and x-ranges overlap or close
            if abs(by1 - py1) < 15 and bx1 <= px2 + 20:
                merged[-1] = (min(px1,bx1), min(py1,by1), max(px2,bx2), max(py2,by2))
                continue
        merged.append(box)

    print(f"  Found {len(merged)} unit label header regions")
    return merged

# ------------------------------------------------------------------
# Main translation
# ------------------------------------------------------------------
def main():
    img = Image.open(IMG_PATH)
    draw = ImageDraw.Draw(img)
    W, H = img.size
    print(f"Image: {W}x{H}")

    WHITE     = (255, 255, 255)
    BLACK     = (0, 0, 0)
    DARK_NAVY = (0, 30, 120)
    BLUE      = (30, 90, 175)
    TITLE_BG  = (251, 240, 158)   # original golden-yellow background

    # ==============================================================
    # 1.  TITLE BLOCK
    # ==============================================================
    # "MẶT BẰNG TẦNG 3A-18"  →  "FLOOR PLAN  FLOORS 3A-18"
    # Title line extends to x=760 based on pixel scan
    draw.rectangle([0, 10, 880, 112], fill=TITLE_BG)
    # Thin white strip at very top to separate from image border
    draw.rectangle([0, 0, 880, 10], fill=WHITE)
    fit_text(draw, (20, 12, 860, 110), "FLOOR PLAN  FLOORS 3A-18",
             bold=True, color=BLUE, max_size=62)

    # "TÒA SYMPHONY 5"  →  "SYMPHONY 5 TOWER"
    # Yellow background extends to x=870, y=110-300
    draw.rectangle([0, 110, 880, 306], fill=TITLE_BG)
    fit_text(draw, (10, 112, 870, 304), "SYMPHONY 5 TOWER",
             bold=True, color=DARK_NAVY, max_size=145)

    # Asterisk notes  (y≈306-420 on white background)
    draw.rectangle([0, 306, 900, 425], fill=WHITE)
    f24 = get_font(22)
    draw.text((8, 310),
              "* DIMENSIONS ARE APPROXIMATE. OFFICIAL DIMENSIONS SPECIFIED IN SIGNED CONTRACT.",
              font=f24, fill=BLACK)
    draw.text((8, 344),
              "* ALL INFORMATION IS VALID AT RELEASE DATE AND MAY BE CHANGED WITHOUT NOTICE.",
              font=f24, fill=BLACK)
    draw.text((8, 378),
              "  SUBJECT TO PRIOR SALE.",
              font=f24, fill=BLACK)

    # ==============================================================
    # 2.  LEGEND BOX  (x=840-1250, y=1400-1760 in original)
    # ==============================================================
    LX1, LY1, LX2, LY2 = 840, 1400, 1250, 1760

    draw.rectangle([LX1, LY1, LX2, LY2], fill=WHITE)
    draw.rectangle([LX1, LY1, LX2, LY2], outline=BLACK, width=3)

    # Header
    HDR_H = 75
    fit_text(draw, (LX1, LY1, LX2, LY1 + HDR_H), "LEGEND",
             bold=True, color=BLACK, max_size=58)
    draw.line([(LX1, LY1+HDR_H), (LX2, LY1+HDR_H)], fill=BLACK, width=2)

    legend_items = [
        ((215, 232, 238), "STUDIO UNIT"),
        ((245, 235, 195), "1-BEDROOM UNIT"),
        ((175, 208, 228), "1-BEDROOM PLUS UNIT"),
        ((240, 190, 205), "2-BEDROOM UNIT"),
    ]
    body_h = LY2 - LY1 - HDR_H
    row_h  = body_h // 4
    pill_w = 145
    pad    = 22

    for i, (color, label) in enumerate(legend_items):
        ry1 = LY1 + HDR_H + i * row_h + 14
        ry2 = ry1 + row_h - 20
        px1 = LX1 + pad
        px2 = px1 + pill_w
        draw.rounded_rectangle([px1, ry1, px2, ry2],
                                radius=18, fill=color, outline=(140,140,140), width=1)
        f38 = get_font(36)
        draw.text((px2 + 18, ry1 + 8), label, font=f38, fill=BLACK)

    # ==============================================================
    # 3.  COMPASS ROSE  "B" → "N"  (top-right area)
    # ==============================================================
    # "B" = Bắc = North. Scanned position: orig x≈3080-3110, y≈115-170
    draw.rectangle([3055, 100, 3145, 185], fill=WHITE)
    f_compass = get_font(72, bold=True)
    draw.text((3060, 105), "N", font=f_compass, fill=BLACK)

    # ==============================================================
    # 4.  UNIT LABELS
    #     Find amber header boxes, then translate "Loại CH" → "Type:"
    #     and "Thông thủy" → "Net Area:" in the rows below each header
    # ==============================================================
    print("Finding unit label boxes...")
    header_boxes = find_unit_label_boxes(img)

    f_label = get_font(20, bold=False)
    translated = 0

    for (hx1, hy1, hx2, hy2) in header_boxes:
        h_height = hy2 - hy1          # header row height
        # Estimate full box: rows below header are ~2.2× header height each
        row_h_est = max(h_height, 25)
        # Row 2 (Loại CH | TYPE) starts just below header
        r2_y1 = hy2 + 1
        r2_y2 = hy2 + row_h_est + 2
        # Row 3 (Thông thủy | AREA) starts below row 2
        r3_y1 = r2_y2 + 1
        r3_y2 = r3_y1 + row_h_est + 2

        box_w = hx2 - hx1
        left_col_w = int(box_w * 0.52)  # "Loại CH" / "Thông thủy" occupies left ~52%

        # --- Row 2: replace "Loại CH" cell ---
        r2_left = (hx1, r2_y1, hx1 + left_col_w, r2_y2)
        draw.rectangle(r2_left, fill=WHITE)
        fit_text(draw, r2_left, "Type:", bold=False, color=BLACK,
                 max_size=22, align="left")

        # --- Row 3: replace "Thông thủy" cell ---
        r3_left = (hx1, r3_y1, hx1 + left_col_w, r3_y2)
        draw.rectangle(r3_left, fill=WHITE)
        fit_text(draw, r3_left, "Net Area:", bold=False, color=BLACK,
                 max_size=22, align="left")

        translated += 1

    print(f"  Translated {translated} unit labels")

    # ==============================================================
    # 5.  Save
    # ==============================================================
    img.save(OUT_PATH, "JPEG", quality=95)
    print(f"\n✓ Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
