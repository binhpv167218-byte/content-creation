# Kế Hoạch Video: Sun Group Tăng Tốc Bàn Giao — Báo Lớn Nói Gì?

**Ngày tạo:** 05/06/2026
**Loại:** HyperFrames Video — 9:16 TikTok/Reels
**Thư mục output:** `studio/video-symphony5-bao-lon/`
**Dự kiến duration:** 75–80 giây
**Nguồn báo:** VietnamNet, Diễn Đàn Doanh Nghiệp, VNExpress

---

## Mục Tiêu Video

Tận dụng chuỗi bài PR của CĐT trên báo lớn để:

1. **Tăng độ tin cậy** — không phải Bình nói, mà báo lớn confirm
2. **Chốt 3 luận điểm** có số thật: tiến độ, booking, cho thuê
3. **Dẫn dắt nhẹ** về Symphony 5 đang nhận booking — không hard-sell

**Tone:** Bình xem báo, thấy số hay, chia sẻ lại góc nhìn của người trong nghề. Không phải PR, là phân tích.

---

## Số Liệu Cốt Lõi Từ Báo (cần highlight trong video)

| #   | Con số                        | Nguồn báo               | Ý nghĩa với nhà đầu tư                                               |
| --- | ----------------------------- | ----------------------- | -------------------------------------------------------------------- |
| 1   | **2 năm**                     | VietnamNet, Diễn đàn DN | S1–S3 ra mắt 05/2024 → bàn giao 05/2026. Đúng hẹn, hiếm trong BĐS VN |
| 2   | **1.669 booking**             | VietnamNet              | Symphony 5 nhận trong ngày khai mạc — tín hiệu cầu thật              |
| 3   | **42 triệu/tháng**            | VietnamNet              | The Panoma (Sun Cosmo) đang cho thuê thật, không là rumor            |
| 4   | **8–9%/năm**                  | VietnamNet              | Tỷ suất cho thuê trung tâm ven sông — cao hơn lãi ngân hàng          |
| 5   | **6 triệu lượt khách** (+19%) | VietnamNet              | 4 tháng đầu 2026 — nền tảng cho thuê ngắn hạn bền vững               |
| 6   | **Sổ đỏ**                     | VietnamNet              | The Panoma đang triển khai cấp — pháp lý sạch, không bị đọng         |

---

## Kỹ Thuật Tạo Highlight Trên Screenshot Báo

### Cách hiển thị screenshot trong HyperFrames:

- Screenshot báo hiện dần từ trái → phải (slide reveal)
- **Highlight overlay:** Rectangle màu vàng/cam (#FFD60A, opacity 0.35) animate in (scaleX 0→1) phủ lên đúng vùng chứa số liệu
- **Zoom-in:** Sau khi highlight, GSAP scale toàn bộ screenshot 1→1.4 vào vùng số
- Logo báo (VietnamNet / Diễn đàn DN) hiện góc trên trái như "nguồn"

### Screenshots cần chụp (user cần làm trước khi implement):

| File cần lưu                               | Báo         | Đoạn cần capture                                | Số liệu cần highlight            |
| ------------------------------------------ | ----------- | ----------------------------------------------- | -------------------------------- |
| `assets/screenshot-vietnamnet-tiendog.png` | VietnamNet  | Đoạn S1-S3 bàn giao tháng 5/2026, chỉ sau 2 năm | "2 năm", "bàn giao tháng 5/2026" |
| `assets/screenshot-vietnamnet-booking.png` | VietnamNet  | Đoạn Symphony 5 nhận 1.669 booking              | "1.669 booking"                  |
| `assets/screenshot-vietnamnet-chothue.png` | VietnamNet  | Đoạn 42 triệu/tháng + 8-9%/năm                  | "42 triệu", "8-9%/năm"           |
| `assets/screenshot-diendandn-phapli.png`   | Diễn Đàn DN | Đoạn pháp lý + tiến độ thần tốc                 | "sổ đỏ", "pháp lý"               |

**Cách chụp chuẩn:**

1. Mở bài báo trên desktop browser (không mobile — text to nhỏ)
2. Zoom browser 125–150% để text rõ
3. Capture vùng 1–2 đoạn văn có chứa số liệu (không cần toàn trang)
4. Kích thước tối thiểu: 1200px ngang
5. Lưu vào `studio/video-symphony5-bao-lon/assets/`

---

## Script VO (Tiếng Việt — MiniMaxi TTS)

> **Model:** `speech-02-hd` | **Voice:** `moss_audio_*` (Vietnamese male, professional)

```
[s0 - HOOK - 0-5s]
Tuần này, ba tờ báo lớn cùng đưa một câu chuyện. Và trong đó có mấy con số mình muốn nói thật.

[s1 - TIẾN ĐỘ - 5-22s]
Tháng năm năm ngoái, Sun Group mở bán Symphony, S1, S2, S3. Tháng năm năm nay — bàn giao. Đúng hai năm. Trong bất động sản Việt Nam, chuyện này không phổ biến. Và báo lớn vừa confirm điều đó.

[s2 - BOOKING - 22-38s]
Symphony 5 vừa ra mắt tháng trước. Nhận một ngàn sáu trăm sáu mươi chín booking ngay trong ngày khai mạc. Con số này không phải CĐT tự nói. Đây là số VietnamNet đưa. Cầu thật, không phải truyền thông.

[s3 - CHO THUÊ - 38-58s]
The Panoma, dự án đã bàn giao trước đó của Sun Group, đang cho thuê bốn mươi hai triệu một tháng. Căn hai phòng ngủ, ven sông Hàn. Tỷ suất tám đến chín phần trăm mỗi năm. Đây là số thật của dự án đã vào tay khách — không phải dự báo.

[s4 - NỀN TẢNG - 58-70s]
Bốn tháng đầu năm, Đà Nẵng đón sáu triệu lượt khách. Tăng mười chín phần trăm. Người thuê là ai, bây giờ bạn đã biết.

[s5 - KẾT - 70-80s]
Mình không nói đảm bảo tăng giá. Nhưng khi báo lớn cùng xác nhận ba điều: tiến độ thật, pháp lý sạch, cho thuê được — đó là bộ bảo chứng đủ để Bình tư vấn khách vào. Symphony 5 đang nhận booking. Bạn muốn nói chuyện cụ thể, nhắn mình.
```

**Tổng duration VO ước tính:** ~75–78 giây

---

## Storyboard — 6 Scenes

### Scene 0 — HOOK (0–5s)

```
Visual: Nền đen. Text dần hiện: "3 tờ báo lớn. Cùng 1 tuần. Cùng 1 câu chuyện."
Logo 3 báo slide in từ dưới: VNExpress · VietnamNet · Diễn Đàn DN
Âm thanh: SFX pop x3 theo từng logo
```

### Scene 1 — TIẾN ĐỘ (5–22s)

```
Visual:
  - Ảnh Bình (binh-portrait-van-phong-ban-do.jpg) — full width, gradient bottom
  - Text overlay: "Đúng 2 năm."
  - Cut sang: Screenshot VietnamNet đoạn bàn giao S1-S3
  - Highlight animate: yellow bar sweep qua "bàn giao tháng 5/2026" và "2 năm"
  - Zoom-in: camera push vào vùng chứa số

GSAP:
  - screenshot slide in từ right (x:200→0, opacity:0→1)
  - highlight bar: scaleX 0→1 từ left, transform-origin left
  - zoom: scale 1→1.35 centered on highlight zone
```

### Scene 2 — BOOKING (22–38s)

```
Visual:
  - Screenshot VietnamNet đoạn "1.669 booking"
  - Highlight: cam đậm (#FF6B35, opacity 0.4) sweep qua "1.669"
  - Counter animation: số 0 → 1.669 (duration 1.5s, ease power2.out)
  - Sub-text: "ngày khai mạc Symphony 5" fade in bên dưới counter

GSAP:
  - Screenshot reveal từ trái (clipPath animate)
  - Counter: textContent update loop
  - Sub-text: y:20→0, opacity:0→1
```

### Scene 3 — CHO THUÊ (38–58s)

```
Visual:
  - Split screen: trái là screenshot VietnamNet đoạn 42 triệu + 8-9%
  - Phải: 2 metric cards animate in
    Card 1: "42 triệu/tháng" — "2PN · The Panoma"
    Card 2: "8–9%/năm" — "tỷ suất cho thuê"
  - Highlight báo: yellow bar qua "42 triệu" và "8-9%"

GSAP:
  - Cards: từ dưới lên (y:40→0), stagger 0.3s
  - Highlight sweep trên screenshot
  - Cards glow nhẹ sau khi hiện (#FFD60A, box-shadow pulse)
```

### Scene 4 — NỀN TẢNG DU LỊCH (58–70s)

```
Visual:
  - Ảnh bãi biển Đà Nẵng (boi-bien-da-nang-skyline.jpg) — full bg
  - Dark overlay 60%
  - Counter: "6.000.000 lượt khách" count up
  - Badge: "+19% so với 2025"
  - Sub: "4 tháng đầu năm 2026 · nguồn VietnamNet"

GSAP:
  - Counter count up 0→6,000,000
  - Badge: scale 0→1 với back.out bounce
```

### Scene 5 — KẾT + CTA (70–80s)

```
Visual:
  - Ảnh Bình (binh-portrait-van-phong-ban-do.jpg)
  - Gradient tối dần từ dưới
  - Text dòng 1: "Tiến độ thật. Pháp lý sạch. Cho thuê được."
  - Text dòng 2 (lime/accent): "Symphony 5 — đang nhận booking"
  - CTA cuối: "Nhắn Bình để nói chuyện cụ thể ↓"

GSAP:
  - Dòng 1: từng từ fade in stagger 0.15s
  - Dòng 2: scale từ 0.8→1, opacity 0→1, màu cam sáng
  - CTA: y:15→0, nhấp nháy nhẹ (opacity 0.7→1 loop)
```

---

## Palette & Typography

```
Nền: #0D0D0D (đen sâu)
Primary accent: #FFD60A (vàng highlight báo)
Secondary accent: #FF6B35 (cam — số liệu quan trọng)
Text: #FFFFFF
Sub-text: rgba(255,255,255,0.7)
Success/credibility: #4CAF50 (dùng cho "sổ đỏ")

Font: Be Vietnam Pro (đã có trong workspace)
  - Counter: 900, 64px
  - Heading: 700, 36px
  - Body: 400, 22px
  - Source tag: 300, italic, 16px
```

---

## Audio

| Track         | File                             | Vai trò                                             |
| ------------- | -------------------------------- | --------------------------------------------------- |
| VO            | `assets/vo_s0.mp3` → `vo_s5.mp3` | MiniMaxi TTS từ script bên trên                     |
| BGM           | `assets/bgm.mp3`                 | Nhẹ, cinematic, không lấn VO — fade in từ 3s, -18dB |
| SFX logo      | `assets/sfx_pop.mp3`             | Scene 0 khi 3 logo hiện                             |
| SFX highlight | `assets/sfx_whoosh.mp3`          | Mỗi lần highlight bar sweep                         |
| SFX counter   | `assets/sfx_tick.mp3`            | Counter animation (optional)                        |

---

## Cấu Trúc Thư Mục

```
studio/video-symphony5-bao-lon/
├── index.html              # HyperFrames composition
├── package.json
├── meta.json
├── gen_vo.py               # MiniMaxi TTS script
├── assets/
│   ├── screenshot-vietnamnet-tiendog.png    ← USER CHUẨN BỊ
│   ├── screenshot-vietnamnet-booking.png    ← USER CHUẨN BỊ
│   ├── screenshot-vietnamnet-chothue.png    ← USER CHUẨN BỊ
│   ├── screenshot-diendandn-phapli.png      ← USER CHUẨN BỊ
│   ├── binh-portrait.jpg                    ← copy từ context/images/
│   ├── danang-beach.jpg                     ← copy từ context/images/
│   ├── vo_s0.mp3 → vo_s5.mp3               ← tạo bằng gen_vo.py
│   ├── bgm.mp3                              ← tìm/dùng từ project cũ
│   ├── sfx_pop.mp3
│   └── sfx_whoosh.mp3
└── renders/
```

---

## Thứ Tự Thực Hiện

### Bước 1 — User chuẩn bị screenshots (15–20 phút)

- [ ] Mở 2 bài báo: VietnamNet + Diễn Đàn DN trên desktop
- [ ] Zoom browser 125%, chụp từng đoạn theo bảng ở trên
- [ ] Lưu vào `studio/video-symphony5-bao-lon/assets/`

### Bước 2 — Claude tạo project folder + gen_vo.py

- [ ] Tạo cấu trúc thư mục
- [ ] Viết `gen_vo.py` với script VO đầy đủ
- [ ] Copy assets từ `context/images/`

### Bước 3 — Chạy gen_vo.py để tạo VO

```bash
cd studio/video-symphony5-bao-lon
python3 gen_vo.py
```

### Bước 4 — Claude viết index.html (HyperFrames composition)

- [ ] 6 scenes theo storyboard
- [ ] GSAP animations: highlight sweep, counter, zoom
- [ ] Screenshot display + highlight overlay
- [ ] Sync VO với từng scene

### Bước 5 — Preview & Chỉnh

```bash
hyperframes preview studio/video-symphony5-bao-lon/
```

### Bước 6 — Render

```bash
hyperframes render studio/video-symphony5-bao-lon/ --output renders/symphony5-bao-lon.mp4
```

---

## Ghi Chú

- VNExpress bị block khi fetch — nếu muốn dùng screenshot VNExpress, chụp thủ công
- Toàn bộ số liệu đã verified từ VietnamNet và Diễn Đàn DN — đáng tin để đưa vào video
- Bàn giao thô (không nội thất) — **không** đề cập trong video này vì context là PR tiến độ, không phải tư vấn chi tiết
- Duration 75–80s là tối ưu cho TikTok dạng "giải thích có dẫn chứng" — không cắt ngắn hơn vì cần đủ thời gian để highlight từng con số có ý nghĩa
