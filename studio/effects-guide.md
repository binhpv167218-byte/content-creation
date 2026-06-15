# Effects Guide — Hướng Dẫn Sử Dụng Hiệu Ứng

> Video Bình Phan BĐS: tone **năng lượng cao** — mạnh, nhanh, có trọng lượng.
> Nguồn hiệu ứng: [[reference-animation-effects]] (7 ambient) + [[reference-animation-effects-p2]] (15 timeline).

---

## Kho Hiệu Ứng Tham Chiếu Nhanh

| #   | Tên                   | Nguồn  | Năng lượng |
| --- | --------------------- | ------ | ---------- |
| A01 | Parallax Layering     | demo-1 | Trung bình |
| A02 | Spotlight Radial Glow | demo-1 | Trung bình |
| A03 | 3D Card Tilt          | demo-1 | Trung bình |
| A04 | Text Shuffle          | demo-1 | **Cao**    |
| A05 | Haptic Bounce         | demo-1 | Trung bình |
| A06 | Image Distortion Wave | demo-1 | Trung bình |
| A07 | Neon Border Draw      | demo-1 | **Cao**    |
| B01 | Mask Wipe Reveal      | demo-2 | **Cao**    |
| B02 | Split Text Cascade    | demo-2 | **Cao**    |
| B03 | Camera Push-In        | demo-2 | **Cao**    |
| B04 | Number Flip Counter   | demo-2 | **Cao**    |
| B05 | Glassmorphism Slide   | demo-2 | Trung bình |
| B06 | Flow Line Connection  | demo-2 | Trung bình |
| B07 | Heat Glow Pulse       | demo-2 | **Cao**    |
| B08 | Orbiting Accents      | demo-2 | Trung bình |
| B09 | Depth Blur Reveal     | demo-2 | Trung bình |
| B10 | Wipe + Overshoot      | demo-2 | **Cao**    |
| B11 | Echo Trail            | demo-2 | **Cao**    |
| B12 | Progress Ring         | demo-2 | Trung bình |
| B13 | Perspective Grid      | demo-2 | Trung bình |
| B14 | Stack Reorder         | demo-2 | Trung bình |
| B15 | Section Sync Beat     | demo-2 | **Cao**    |

---

## Theo Loại Scene

## Combo Hook Đã Duyệt — Chỉ Dùng Các Mẫu Này

> Đoạn mở đầu (hook) chỉ được làm theo các combo đã duyệt dưới đây.
> File demo: `studio/video-hook-combos/`

### COMBO 0 — "Danang Opening" ✅ DUYỆT (video-danang)

**Hiệu ứng:** A07 Neon Border Draw (primary) + B04 Number Counter (primary) + B07 Glow Pulse (micro)

**Cảm giác:** Số lớn đập vào mắt + viền neon frame toàn màn hình → trọng lượng, tin tức

**Pattern GSAP:**

```js
// 1. BG fade + scene blur-in
tl.from(
  "#s0",
  {
    opacity: 0,
    scale: 0.94,
    filter: "blur(16px)",
    duration: 0.7,
    ease: "power2.out",
  },
  0,
);
// 2. Neon border vẽ viền toàn màn (sync với beat đầu tiên)
tl.to(
  "#neon-path",
  { strokeDashoffset: 0, duration: 2.5, ease: "power2.inOut" },
  0.476,
);
// 3. Eyebrow + divider
tl.from("#eyebrow", { y: -28, opacity: 0, duration: 0.4 }, 0.476);
tl.from(
  "#hdiv",
  { scaleX: 0, opacity: 0, duration: 0.45, transformOrigin: "center" },
  0.7,
);
// 4. Số đập vào (scale + counter) theo beat
tl.call(playImpact, [], 1.091);
tl.from(
  "#num",
  { scale: 0.65, opacity: 0, duration: 0.7, ease: "back.out(1.7)" },
  1.091,
);
tl.to(
  { v: 0 },
  {
    v: 17.3,
    duration: 0.8,
    ease: "power2.out",
    onUpdate: function () {
      num.textContent = this.targets()[0].v.toFixed(1);
    },
  },
  1.091,
);
// 5. Unit, sub, tag stagger lên
tl.from("#unit", { y: 24, opacity: 0, duration: 0.4, ease: "expo.out" }, 1.707);
tl.from("#sub", { y: 28, opacity: 0, duration: 0.45 }, 2.322);
tl.from(
  "#tag",
  { scale: 0.8, opacity: 0, duration: 0.4, ease: "back.out(1.7)" },
  2.926,
);
// 6. Glow pulse lặp
tl.to(
  "#num",
  {
    textShadow: "0 0 70px rgba(255,209,102,0.85),...",
    duration: 1.2,
    yoyo: true,
    repeat: 2,
  },
  3.529,
);
// 7. Neon fade out trước khi cắt scene
tl.to("#neon-path", { opacity: 0, duration: 0.5 }, 6.2);
```

**Dùng khi:** Video thị trường, số liệu lớn cần credibility cao (tỷ suất, lượng khách, giá)

**SFX:** `fs_swoosh_air.mp3` (entry) + `fs_bright_hit.mp3` (số land) — Freesound CC0

---

### COMBO A — "Echo Slam" ✅ DUYỆT (video-hook-combos)

**Hiệu ứng:** B11 Echo Trail (primary) + B04 Number Counter (secondary) + B07 Glow Pulse (micro) + Neon cyan border

**Cảm giác:** Số lao vào từ trái với 3 ghost layers → counter settle → glow warm — năng lượng cao, tích cực

**Màu sắc:**

- Số chính: `#FFE566` (vàng nắng)
- Ghost layers: `#00E5E8` (cyan biển)
- Unit text: trắng + glow cyan
- Neon border: `#00E5E8`, stroke-width 10, 3 lớp drop-shadow

**Pattern GSAP (tóm tắt):**

```js
// 4 echo layers fly từ x:-900, back.out(2.0), stagger 0.045
tl.fromTo(["#ghost3","#ghost2","#ghost1","#main"], { x:-900 },
  { x:0, duration:0.55, ease:"back.out(2.0)", stagger:0.045 }, 0.20);
// Counter 0 → số thật
tl.to({v:0}, { v:TARGET, duration:0.48, ease:"power2.out", onUpdate:... }, 0.55);
// Bounce landing
tl.to("#main", { scale:1.08, duration:0.10 }, 0.72);
tl.to("#main", { scale:1.0, duration:0.40, ease:"elastic.out(1.2,0.5)" }, 0.82);
// Glow pulse warm
tl.to("#main", { textShadow:"0 0 80px rgba(255,220,80,0.9)...", duration:0.6, yoyo:true, repeat:3 }, 2.2);
```

**SFX:** `fs_swoosh_air.mp3` (entry t=0.18) + `fs_bright_hit.mp3` (impact t=0.72, t=1.10) — Freesound CC0

**Dùng khi:** Số liệu thị trường, lượt khách, bất kỳ con số cần năng lượng cao

---

### COMBO C — "Shock Zoom" ✅ DUYỆT (video-hook-combos)

**Hiệu ứng:** Visual Shock Zoom (primary) + B04 Text Shuffle (secondary) + B07 Glow Pulse (micro) + Neon cyan border

**Cảm giác:** Số xuất hiện từ cực nhỏ bùng ra toàn màn hình → text shuffle settle → sunrise glow — dramatic nhưng tích cực

**Màu sắc:** Giống COMBO A — `#FFE566` số, `#00E5E8` neon, sunrise burst warm orange

**Pattern GSAP (tóm tắt):**

```js
// Sunrise burst
tl.fromTo(
  "#burst",
  { opacity: 0.95, scale: 0.5 },
  { opacity: 0, scale: 1.8, duration: 0.65, ease: "power2.out" },
  t,
);
// SHOCK ZOOM: 0.06 → 9 → 0.95
tl.fromTo(
  "#num",
  { scale: 0.06 },
  { scale: 9, duration: 0.24, ease: "power3.in" },
  t,
);
tl.to(
  "#num",
  { scale: 0.95, duration: 0.5, ease: "elastic.out(1.0,0.45)" },
  t + 0.24,
);
// Text shuffle (seeded PRNG) → số thật
// Glow settle
tl.to(
  "#num",
  {
    textShadow: "0 0 90px rgba(255,220,80,1), 0 0 60px rgba(0,229,232,0.35)",
    scale: 1.0,
  },
  t + 1.05,
);
```

**SFX:** `fs_hit_whoosh.mp3` (t=0.00) + `fs_bright_hit.mp3` (settle t=1.05) — Freesound CC0

**Dùng khi:** Booking, số milestone lớn cần "wow moment" — Symphony 5, số ra mắt, kỷ lục

---

### Ghi Chú Chung — Hook Combos

- **Neon border** bắt buộc ở mọi combo — cyan `#00E5E8`, stroke-width 10, 3 lớp glow
- **Overlay** nhạt (gradient bottom-to-top, max 82%) — để background thấy rõ
- **Âm thanh sóng biển thật quá ồn** — dùng `fs_bright_hit` + `fs_swoosh_air` (bright, airy, không tối)
- **Bounce animation** (`elastic.out`, `back.out`) thay vì slam nặng

---

## Combo Outro/CTA ✅ DUYỆT (video-danang)

> Tham chiếu: scene S4 của `video-danang` (giây 45–57)

### Layout — Thứ Tự Bắt Buộc

```
[Brand name: Bình Phan IQI]   ← TRÊN ảnh
[Avatar 336×336 circle]        ← DƯỚI brand name
```

**Không có subtitle** — bỏ "Chuyên gia BĐS", "IQI Đà Nẵng", số điện thoại. Chỉ cần brand name.

### Brand Name CSS

```css
.cta-contact-name {
  font-size: 34px;
  font-weight: 600;
  color: #ffffff; /* "Bình Phan" — trắng */
}
/* "IQI" bọc trong <span style="color:#FFD966"> */
```

```html
<div class="cta-contact-name">
  Bình Phan <span style="color: #FFD966">IQI</span>
</div>
<img class="cta-avatar" src="assets/me-outtro.jpg" alt="" />
```

### Avatar CSS

```css
.cta-avatar {
  width: 336px;
  height: 336px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid rgba(255, 209, 102, 0.6);
  box-shadow: 0 0 40px rgba(255, 209, 102, 0.3);
}
```

### Background — Morph Blob

Nền CTA dùng blob CSS animation (không dùng ảnh):

```css
.morph-bg {
  position: absolute;
  width: 720px;
  height: 720px;
  border-radius: 60% 40% 30% 70%/60% 30% 70% 40%;
  background: radial-gradient(
    circle,
    rgba(255, 209, 102, 0.1) 0%,
    transparent 70%
  );
  z-index: 0;
  animation: morphBg 7s ease-in-out infinite;
}
@keyframes morphBg {
  0%,
  100% {
    border-radius: 60% 40% 30% 70%/60% 30% 70% 40%;
  }
  33% {
    border-radius: 30% 70% 70% 30%/30% 40% 60% 70%;
  }
  66% {
    border-radius: 50% 50% 30% 70%/40% 60% 40% 60%;
  }
}
```

### Animation Sequence

```js
// 1. Scene enter: blur + scale
tl.from(
  "#cta",
  { opacity: 0, scale: 0.94, filter: "blur(12px)", duration: 0.65 },
  t,
);
// 2. Label fade down
tl.from("#label", { y: -20, opacity: 0, duration: 0.4 }, t + 0.6);
// 3. Title bounce up
tl.from(
  "#title",
  { y: 40, opacity: 0, scale: 0.91, duration: 0.65, ease: "expo.out" },
  t + 1.2,
);
// 4. Stats stagger up (nếu có)
tl.from(
  ".stat",
  { y: 22, opacity: 0, stagger: 0.14, duration: 0.4, ease: "back.out(1.5)" },
  t + 1.8,
);
// 5. CTA button bounce
tl.from(
  "#btn",
  { scale: 0.78, opacity: 0, duration: 0.45, ease: "back.out(1.7)" },
  t + 3.0,
);
// 6. Contact block (brand name + avatar)
tl.from("#contact", { y: 14, opacity: 0, duration: 0.35 }, t + 3.7);
```

---

## Combo Screenshot — Chuẩn Bắt Buộc

> Mỗi khi dùng ảnh chụp màn hình báo/tài liệu trong video, áp dụng đúng pattern này.
> Tham chiếu: scene s2 (giây 19–28) và s3 (giây 28–40) của `video-symphony5-bao-lon`.

### Kích Thước Card

```css
.news-card {
  width: 100%; /* full width vùng scene */
  height: auto; /* giữ nguyên tỉ lệ ảnh chụp */
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.85);
  clip-path: inset(0 100% 0 0); /* ẩn ban đầu — animate vào */
}
.news-card img {
  display: block;
  width: 100%;
  height: auto;
}

/* Highlight bar — đè lên dòng text quan trọng trong screenshot */
.news-hl {
  position: absolute;
  left: 10px;
  right: 10px;
  height: 46px;
  background: rgba(255, 214, 10, 0.4); /* vàng — dùng cho số liệu */
  border-radius: 4px;
  transform: scaleX(0);
  transform-origin: left;
  z-index: 2;
}
.news-hl.red {
  background: rgba(240, 90, 60, 0.38);
} /* đỏ — dùng cho pháp lý, cảnh báo */

/* Source bar — logo báo ở góc dưới card */
.news-src-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 10px 18px;
  background: rgba(2, 12, 24, 0.88);
  font-size: 20px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  gap: 8px;
}
```

### Thứ Tự Animation (6 bước cố định)

```js
// 1. Scene enter: blur-in + scale
tl.fromTo(
  "#scene",
  { opacity: 0, filter: "blur(8px)", scale: 0.97 },
  {
    opacity: 1,
    filter: "blur(0px)",
    scale: 1,
    duration: 0.52,
    ease: "power2.out",
  },
  t,
);

// 2. Eyebrow (nguồn báo) slide từ trái
tl.fromTo(
  "#eyebrow",
  { x: -28, opacity: 0 },
  { x: 0, opacity: 1, duration: 0.38, ease: "power3.out" },
  t + 0.5,
);

// 3. Card reveal — Mask Wipe TOP → BOTTOM
tl.fromTo(
  ".news-card",
  { clipPath: "inset(0% 0 100% 0)" },
  { clipPath: "inset(0% 0 0% 0)", duration: 0.6, ease: "power2.inOut" },
  t,
);

// 4. Quote/stat card trượt từ phải — Glassmorphism Slide
tl.fromTo(
  "#quote-card",
  { x: 200, opacity: 0 },
  { x: 0, opacity: 1, duration: 0.62, ease: "back.out(1.4)" },
  t + 0.5,
);

// 5. Highlight bar sweep — tại thời điểm VO nói con số/từ khóa quan trọng
tl.fromTo(
  ".news-hl",
  { scaleX: 0 },
  { scaleX: 1, duration: 0.72, ease: "power2.inOut", transformOrigin: "left" },
  t_highlight,
);

// 6. Card exit — wipe trái (khác hướng vào)
tl.fromTo(
  ".news-card",
  { clipPath: "inset(0 0 0 0%)" },
  { clipPath: "inset(0 0 0 100%)", duration: 0.5, ease: "power2.in" },
  t_exit,
);
```

### Highlight Bar — Định Vị

Chỉnh `top: XX%` theo vị trí dòng text trong ảnh chụp:

- Dòng ở giữa ảnh → `top: 45–55%`
- Dòng cuối ảnh → `top: 70–80%`
- Dòng đầu ảnh → `top: 15–25%`

Luôn để ghi chú `<!-- top % cần chỉnh sau khi có ảnh thật -->` trong HTML.

---

### 🔴 HOOK (0–5s) — Phải dừng ngón tay ngay lập tức

Mục tiêu: shock thị giác trong 0.3s đầu. Không dùng hiệu ứng nhẹ.

**Hiệu ứng ưu tiên:**

- **B03 Camera Push-In** — cảm giác "lao vào" ngay từ giây đầu, mạnh nhất cho hook
- **B01 Mask Wipe Reveal** — text/số lộ ra bất ngờ, rất sắc
- **B11 Echo Trail** — số liệu lớn lao vào kèm vệt bóng → cinematic
- **A04 Text Shuffle** — chữ matrix settle thành con số thật → tạo tò mò

**Kết hợp chuẩn cho hook năng lượng cao:**

```
B03 (camera push) + B01 (mask wipe text) + A07 (neon border)
```

**Tránh ở hook:** A01 Parallax (quá nhẹ), B09 Depth Blur (quá chậm), B08 Orbiting (phân tán ánh nhìn)

---

### 📊 DATA SCENE — Số liệu, thị trường, con số cụ thể

Mục tiêu: con số phải nổi bật, đáng tin, dễ đọc khi lướt nhanh.

**Hiệu ứng ưu tiên:**

- **B04 Number Flip Counter** — xáo trộn rồi settle về số thật → **bắt buộc cho mọi data scene**
- **B12 Progress Ring** — % tỷ suất, tỷ lệ → trực quan ngay
- **B07 Heat Glow Pulse** — highlight vùng số quan trọng, dẫn mắt
- **A07 Neon Border Draw** — đóng khung số liệu, tăng credibility
- **B06 Flow Line Connection** — kết nối nhiều data points với nhau

**Kết hợp chuẩn:**

```
B04 (counter) + B07 (glow pulse trên số) + B12 (ring nếu có %)
```

---

### 📰 SCREENSHOT/QUOTE SCENE — Dẫn chứng từ báo, trích dẫn

Mục tiêu: tăng độ tin cậy — "không phải mình nói, báo confirm".

**Hiệu ứng ưu tiên:**

- **B01 Mask Wipe Reveal** — screenshot lộ ra từ trái sang phải như đang đọc báo
- **B07 Heat Glow Pulse** — highlight đúng vùng chứa số quan trọng trong screenshot
- **B03 Camera Push-In** — zoom vào vùng số sau khi reveal → drama

**Kết hợp chuẩn:**

```
B01 (reveal screenshot) → B07 (glow vùng số) → B03 (zoom in)
```

---

### 🏙️ PROJECT SHOWCASE — Giới thiệu dự án BĐS

Mục tiêu: dự án phải trông premium, đáng tiền.

**Hiệu ứng ưu tiên:**

- **A03 3D Card Tilt** — card dự án tự nghiêng → chiều sâu, sang trọng
- **B05 Glassmorphism Slide** — thông tin kỹ thuật (diện tích, giá) trượt vào mượt
- **B09 Depth Blur Reveal** — ảnh dự án đi vào focus từ blur → cinematic
- **A01 Parallax Layering** — ảnh dự án có chiều sâu khi kể chuyện
- **B14 Stack Reorder** — so sánh nhiều phân khu/loại căn

**Kết hợp chuẩn:**

```
B09 (depth blur reveal ảnh) + A03 (3D tilt card thông tin) + B05 (glassmorphism chi tiết)
```

---

### 📖 STORY/CONTEXT SCENE — Kể chuyện, kinh nghiệm nghề

Mục tiêu: người xem cảm nhận được "người thật việc thật".

**Hiệu ứng ưu tiên:**

- **B02 Split Text Cascade** — từng từ rơi xuống như đang nói chuyện
- **A01 Parallax Layering** — ảnh chân dung Bình có chiều sâu nhẹ
- **B13 Perspective Grid** — tạo không gian, backdrop cho storytelling
- **A02 Spotlight Radial Glow** — highlight vùng text quan trọng tự động

**Kết hợp chuẩn:**

```
A01 (parallax bg) + B02 (split text) + A02 (spotlight trên câu chốt)
```

---

### ⚡ CTA (Khúc Cuối) — Bình Phan IQI

Mục tiêu: kết mạnh, người xem nhớ tên, muốn inbox.

**Hiệu ứng ưu tiên:**

- **B15 Section Sync Beat** — beat nhạc trigger micro-action → energy cao nhất khi kết
- **B10 Wipe + Overshoot** — CTA text vào với lực mạnh, back.out rõ
- **B07 Heat Glow Pulse** — tên "Bình Phan IQI" glow nhẹ → memorable
- **A05 Haptic Bounce** — avatar/logo bounce để kéo mắt vào CTA

**Kết hợp chuẩn:**

```
B10 (wipe text CTA vào) + B07 (glow tên) + B15 (sync beat cuối)
```

---

## Quy Tắc Phối Hợp

### Công thức 1 scene = 1 primary + 1 secondary + 1 micro

| Vai trò       | Định nghĩa                              | Ví dụ                        |
| ------------- | --------------------------------------- | ---------------------------- |
| **Primary**   | Hiệu ứng chính — mắt nhìn vào đây trước | B04 Counter, B03 Camera Push |
| **Secondary** | Hỗ trợ primary — tăng chiều sâu         | B07 Glow, B01 Mask Wipe      |
| **Micro**     | Accent nhỏ — texture, không cạnh tranh  | A05 Haptic, A07 Neon Border  |

### Cặp Hợp Lý (đã test)

| Primary            | Secondary      | Micro             | Scene phù hợp    |
| ------------------ | -------------- | ----------------- | ---------------- |
| B03 Camera Push-In | B01 Mask Wipe  | A07 Neon Border   | Hook             |
| B04 Number Flip    | B07 Glow Pulse | B12 Progress Ring | Data             |
| B02 Split Text     | A01 Parallax   | A02 Spotlight     | Story            |
| B09 Depth Blur     | A03 3D Tilt    | B05 Glassmorphism | Project          |
| B10 Wipe Overshoot | B07 Glow Pulse | B15 Sync Beat     | CTA              |
| B11 Echo Trail     | B04 Counter    | A07 Neon Border   | Hook số liệu lớn |

### Quy Tắc Cứng

- **Không quá 3 hiệu ứng/scene** — quá 3 là loạn mắt
- **Không dùng 2 "Cao" làm primary+secondary cùng lúc** — chọn 1 cái làm chủ đạo
- **Hook phải có ít nhất 1 hiệu ứng "Cao"** — không thương lượng
- **CTA chỉ dùng hiệu ứng đã xuất hiện trong video** — consistency, không introduce hiệu ứng mới ở phút cuối
- **Không lặp cùng primary 2 scene liên tiếp** — B03 ở scene 1 xong thì scene 2 phải dùng primary khác

### Trình Tự Năng Lượng Chuẩn Cho Video BĐS

```
HOOK (cao) → DATA (cao) → STORY (trung bình) → PROJECT (trung bình) → CTA (cao)
```

Năng lượng không đi thẳng từ cao xuống thấp — phải có nhịp lên xuống, kết bằng cao.

---

## Checklist Trước Khi Chọn Hiệu Ứng

- [ ] Scene này là loại nào? (hook/data/story/project/CTA)
- [ ] Primary effect đã chọn chưa?
- [ ] Secondary có hỗ trợ primary hay cạnh tranh?
- [ ] Scene trước dùng primary gì? Không được lặp
- [ ] Tổng số hiệu ứng ≤ 3?
- [ ] CTA chỉ dùng hiệu ứng đã xuất hiện trước đó?
