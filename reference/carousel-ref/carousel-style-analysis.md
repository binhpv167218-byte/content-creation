# Phân Tích Style Carousel

_Cập nhật: 2026-05-08 — Viết lại theo style q1-q6_

> **File tham chiếu:** `q1.jpg` – `q6.jpg` — portrait carousel của người trong nghề BĐS

---

## Tổng Quan Style

**Dark portrait photo overlay** — ảnh chân dung của Bình full-bleed, mặt nhìn rõ ở phần trên slide. Overlay gradient (trong suốt trên → tối dưới). Số thứ tự lime to ở bên trái, heading trắng đậm bên phải, body text full-width phía dưới.

---

## Kích Thước

**1080 × 1620 px** (tỉ lệ 2:3) — khớp với reference q1-q6, phù hợp Facebook + TikTok.

---

## Màu Sắc

| Yếu tố           | Giá trị             | Ghi chú                                    |
| ---------------- | ------------------- | ------------------------------------------ |
| Số thứ tự        | Lime `#C8E64A`      | Thay cho gold `#D4850A` trong bản gốc      |
| Category label   | Lime `#C8E64A`      | ALL CAPS, nhỏ                              |
| Heading          | Trắng `#FFFFFF`     | Bold, lớn                                  |
| Body text        | Trắng `#FFFFFF`     | Regular                                    |
| Subtitle cover   | Off-white `#F0F0F0` | Nhẹ hơn heading                            |
| Takeaway/closing | Lime `#C8E64A`      | Italic, dòng cuối nổi bật                  |
| Brand logo B·P   | Trắng `#FFFFFF`     | Bold, 62pt, top-right                      |
| Overlay gradient | Black alpha 10→215  | Gần trong suốt ở trên → tối dần xuống dưới |

---

## Typography — Be Vietnam Pro

| Cấp độ         | Weight   | Size  | Ghi chú                                        |
| -------------- | -------- | ----- | ---------------------------------------------- |
| Brand "B·P"    | Bold     | 62pt  | Top-right, shadow nhẹ                          |
| Cover title    | Bold     | 72pt  | Wrap tự động, shadow                           |
| Số thứ tự      | Bold     | 310pt | 1 chữ số; 240pt nếu 2 chữ số                   |
| Category label | SemiBold | 22pt  | ALL CAPS, lime — optional (JSON field `label`) |
| Heading        | Bold     | 50pt  | Auto-reduce đến 34pt nếu quá 4 dòng            |
| Body text      | Regular  | 22pt  | White, line height ×1.55                       |
| Takeaway       | Italic   | 21pt  | Lime color                                     |
| CTA heading    | Bold     | 62pt  | Centered                                       |
| Author name    | SemiBold | 32pt  | Centered, CTA slide                            |
| Author role    | Light    | 22pt  | Centered, gray                                 |

---

## Layout Constants

```
W = 1080, H = 1620
MARGIN = 60          # left/right padding
NUM_Y  = 660         # number zone starts here (≈40% of H)
BODY_GAP = 28        # gap between separator dot and body text start
```

---

## Cấu Trúc Slide

### Cover

```
[0–40%]  Ảnh chân dung Bình + gradient overlay nhẹ → face rõ
[40%]    Lime accent bar (80×5px)
[40%+]   Title (Bold 72pt, white, wrap)
         Lime rule (96×4px)
         Subtitle (Regular 26pt, off-white)
[bottom] "vuốt để xem →" (Light 22pt, gray)
```

### Content Slide (q1-q6 match)

```
[0–40%]  Ảnh chân dung + gradient → face visible
[40%]    ┌──────────────────────────────────────────────┐
         │ LARGE NUMBER (Lime 310pt)  │ LABEL (Lime 22pt CAPS) │
         │                            │ Heading (White Bold 50pt)│
         │  ● (lime dot below num)    │ ● (white dot separator)  │
         └──────────────────────────────────────────────┘
[below]  Body text full-width (White Regular 22pt)
         Bullet lines với "• " → indent 28px
         **word** → lime inline highlight
[closing] Takeaway (Lime Italic 21pt)
```

### CTA

```
[0–40%]  Ảnh + gradient → face visible
[40%]    Lime accent bar
         Heading centered (Bold 62pt, white)
         Lime rule centered
         Subtitle centered (Italic 25pt, off-white)
[bottom] Author divider line
         "Bình Phan" (SemiBold 32pt)
         "IQI Đà Nẵng · 0905 436 789" (Light 22pt, gray)
         3 lime dots
```

---

## Gradient Overlay

```python
# Accelerating curve: nearly transparent at top → dark at bottom
for y in range(H):
    t = y / H
    alpha = int(10 + (215 - 10) * (t ** 1.6))
    # painted pixel-by-pixel as 1D gradient resized to full width
```

---

## Ảnh Nền

- **Crop mode:** top-biased (15% offset) để giữ mặt ở trên
- **Chất lượng:** LANCZOS resize
- **Khuyến nghị:** dùng ảnh chân dung Bình đứng (`IMG_7928.jpg`) cho mọi carousel
- **Không dùng:** ảnh phong cảnh, ảnh nhóm, ảnh selfie close-up

---

## CLI Usage

```bash
python3 scripts/generate-carousel.py \
  --json posts/NNN-slug/content.json \
  --output posts/NNN-slug/carousel.pdf \
  --photo context/images/IMG_7928.jpg
```

---

## JSON Format Chuẩn

```json
{
  "title": "Tiêu đề cover",
  "slides": [
    {
      "number": "00",
      "heading": "Tiêu đề cover (dự phòng)",
      "subtitle": "Subtitle hiển thị dưới title trên cover",
      "takeaway": "Tagline"
    },
    {
      "number": "01",
      "label": "TÊN CATEGORY (tùy chọn)",
      "heading": "Heading ngắn gọn",
      "subtitle": "Body text. Hỗ trợ **lime highlight**.\n\n• Bullet point 1\n• Bullet point 2",
      "takeaway": "Câu kết luận in lime italic."
    },
    {
      "number": "",
      "heading": "CTA heading",
      "subtitle": "CTA subtitle",
      "takeaway": ""
    }
  ]
}
```

- `"00"` → cover subtitle, không tạo content slide
- `""` → CTA slide cuối
- `label` → optional category label (ALL CAPS, lime, trên heading)
- `**word**` → inline lime trong subtitle/takeaway
- `• ` đầu dòng → bullet với indent

---

## File Tham Chiếu

| File     | Nội dung                                          |
| -------- | ------------------------------------------------- |
| `q1.jpg` | Slide 1 — "GIÁ TRỊ TỪ TAM QUAN" — full layout mẫu |
| `q2.jpg` | Slide 3 — "KHẢ NĂNG BIỂU ĐẠT"                     |
| `q3.jpg` | Slide 3 — alt pose                                |
| `q4.jpg` | Slide 2 — "ĐIỂM YẾU"                              |
| `q5.jpg` | Slide 5 — "CỐT TRUYỆN"                            |
| `q6.jpg` | Slide 5 — alt                                     |
