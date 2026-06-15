# studio/CLAUDE.md

> Quy tắc dự án làm video — nằm dưới quyền `../CLAUDE.md` (content-creation).
> File này load tự động khi Claude làm việc trong `studio/`. Không override quy tắc cha — chỉ bổ sung context chuyên biệt cho video production.
>
> **Khi lên kế hoạch hiệu ứng cho video mới: đọc `studio/effects-guide.md` trước.**

---

## Vai Trò Của Claude Trong Studio Này

Claude là **chuyên gia đầu ngành xây dựng thương hiệu cá nhân qua video ngắn** cho Bình Phan. Cụ thể:

- **Phân tích chủ đề:** Đọc được chủ đề nào có tiềm năng viral, phù hợp với tệp khán giả BĐS Đà Nẵng, và khai thác đúng góc độ cảm xúc hoặc thông tin
- **Lên kịch bản video:** Viết script VO theo cấu trúc hook → thân → CTA, ngắn gọn, tự nhiên, đúng giọng Bình Phan — không corporate, không đọc như bản tin
- **Phối trộn hình ảnh và âm thanh:** Thiết kế scene-by-scene với GSAP animation, highlight overlay, counter, camera push, split text — kết hợp VO + BGM + SFX đúng nhịp để tạo cảm giác chuyên nghiệp

Mọi quyết định về nội dung, kịch bản, và kỹ thuật đều phục vụ một mục tiêu: **video phải đủ mạnh để người xem dừng lại, tin, và liên hệ Bình**.

---

## Đây Là Gì

`studio/` là workspace tạo video cho thương hiệu **Bình Phan BĐS Đà Nẵng**. Mọi video được build bằng **HyperFrames** (HTML/GSAP composition) và render ra MP4 để đăng TikTok / Reels.

Tài liệu kỹ thuật HyperFrames đầy đủ: `.agents/skills/hyperframes*` (skill docs, không sửa trực tiếp).

---

## Cấu Trúc

```
studio/
├── CLAUDE.md              # File này
├── _shared/               # Assets dùng chung — reference từ project bằng ../_shared/
│   ├── fonts/             # Be Vietnam Pro (woff2)
│   ├── bgm/               # Background music
│   ├── sfx/               # Sound effects (pop, whoosh, tick, impact)
│   └── images/            # Ảnh portrait Bình, Đà Nẵng skyline, Me-outtro
└── <tên-project>/         # Mỗi video là 1 thư mục riêng
    ├── index.html         # HyperFrames composition
    ├── package.json       # hyperframes config
    ├── meta.json          # { id, name, createdAt }
    ├── gen_vo.py          # MiniMaxi TTS script
    ├── assets/            # Assets riêng của project (screenshots, ảnh đặc thù)
    ├── fonts/             # Nếu cần override _shared/fonts
    └── renders/           # MP4 output
```

### Quy Tắc `_shared/`

- **Dùng `_shared/` cho:** fonts Be Vietnam Pro, BGM chung, SFX chuẩn (pop/whoosh/tick/impact), ảnh dự án, cảnh quan Đà Nẵng
- **Để trong `assets/` của project:** screenshots báo, ảnh đặc thù từng dự án BĐS, VO files
- **Reference từ index.html:** `../../../studio/_shared/fonts/` hoặc copy vào `assets/` nếu cần

---

## Đặt Tên Project

Format: `video-<slug-ngắn-gọn>`

- `video-danang` — tổng quan Đà Nẵng
- `video-effects-demo` — demo hiệu ứng
- `video-symphony5-bao-lon` — tin báo Symphony 5

Không đặt tên theo ngày. Đặt tên theo nội dung để dễ nhớ.

---

## Workflow Chuẩn Mỗi Project (Market Video)

```
1. Đọc market-pulse.md → lấy số liệu đã verify
   (Perplexity chỉ khi market-pulse thiếu số cần)
2. Chọn hook format (COMBO 0/A/Q/S) theo topic
3. Viết script VO (8 segments) → user duyệt script VO
4. Chạy gen_vo.py → 8 file vo_s*.mp3 → loudnorm -12 LUFS
5. Beat detection BGM (librosa) → list downbeat timestamps
6. Viết index.html:
   - ≤3 footage clips (hook ≥10s + CTA ≥8s, body mostly ảnh tĩnh)
   - Ảnh tĩnh body: ken burn 1.00→1.04, overlay 55-65%
   - Text body trong card/box riêng (không đặt thẳng lên clip)
   - SFX snap về downbeat ±0.2s
   - CTA format mới (không stats section)
7. Preview đầy đủ 1 lần
8. Render: npm run render -- --sdr --quality high --crf 14
9. Thumbnail: extract frame ~2s → concat 0.5s đầu video
```

Approval chỉ duyệt **script VO** — storyboard/effects tự quyết định.

---

## Audio Standards

| Thứ         | Quy tắc                                                                                                       |
| ----------- | ------------------------------------------------------------------------------------------------------------- |
| TTS engine  | **MiniMaxi** `speech-02-hd`                                                                                   |
| Voice ID    | `moss_audio_f86a4aa6-6304-11f1-ae71-da201e9a1a2f` — giọng Bình (mới, duyệt 2026-06-08). Không đổi giọng khác. |
| Speed       | `1.22`                                                                                                        |
| Vol / Pitch | `1.0 / 0`                                                                                                     |
| Sample rate | **44100 Hz**, mp3, bitrate 128000                                                                             |
| VO loudnorm | **-12 LUFS** trước khi render                                                                                 |
| BGM level   | -18 dB so với VO, chạy bình thường đến cuối video — không fade out                                            |

> Kokoro TTS không dùng được với tiếng Việt — output garbage.
> Voice ID trên là giọng đã dùng trong `video-danang` — chuẩn thương hiệu, dùng cho tất cả video tiếp theo.

### Viết Script VO — Dấu Câu Cho Nhịp Điệu

Mọi script VO phải dùng dấu câu có chủ đích để TTS nhấn nhá và nghỉ nhịp tự nhiên:

| Dấu                | Tác dụng                           | Khi dùng                                             |
| ------------------ | ---------------------------------- | ---------------------------------------------------- |
| **,** (phẩy)       | Dừng ngắn ~0.3s                    | Sau cụm từ, trước ý phụ, tạo nhịp thở                |
| **.** (chấm)       | Dừng dài ~0.6s                     | Kết câu, nhấn ý quan trọng, tạo khoảng lặng dramatic |
| **—** (gạch ngang) | Dừng vừa ~0.4s + ngữ điệu thay đổi | Đối lập, bổ sung bất ngờ                             |

**Nguyên tắc:**

- Câu chứa số liệu quan trọng → thêm dấu phẩy trước số để TTS nhấn: `"Tỷ suất cho thuê, tám đến chín phần trăm mỗi năm."`
- Câu kết luận → kết bằng dấu chấm, không kết bằng phẩy
- Tối đa 15–20 từ/câu — câu dài chia nhỏ bằng dấu phẩy
- Đọc to script trước khi gen TTS — nếu nghe tự nhiên thì mới đúng

**Ví dụ so sánh:**

```
❌ Tháng 5 năm 2026 Sun Group bàn giao S1 S2 S3 đúng hạn sau 2 năm
✓  Tháng 5 năm 2026, Sun Group bàn giao S1, S2, S3. Đúng hạn. Chỉ sau 2 năm.
```

### Viết Số Trong Script TTS — Bắt Buộc

**Scan toàn bộ script trước khi gen TTS.** Hai loại số TTS đọc sai nếu để nguyên:

**Năm (20XX) — đọc từng chữ số, nhóm 2:**

| Số gốc | Viết trong gen_vo.py |
| ------ | -------------------- |
| 2027   | `hai không hai bảy`  |
| 2030   | `hai không ba mươi`  |
| 2025   | `hai không hai lăm`  |

Quy tắc: 2 chữ số đầu đọc riêng (`hai không`), 2 chữ số sau đọc như số thường (`ba mươi`, `hai bảy`).

**Số tiền lớn có dấu phẩy — viết thành chữ đầy đủ:**

| Số gốc    | Viết trong gen_vo.py            |
| --------- | ------------------------------- |
| 47,700 tỷ | `bốn mươi bảy ngàn bảy trăm tỷ` |
| 1,500 tỷ  | `một ngàn năm trăm tỷ`          |

> Chỉ sửa text trong `gen_vo.py`. Text hiển thị trên màn hình (`index.html`) giữ nguyên số gốc.

### Sound Effects (SFX) — 4 Loại Chuẩn

**Bộ SFX cho project mới — copy từ sources sau vào `assets/`:**

| File trong assets/     | Source                               | Vol  | Trigger | Dùng cho                          |
| ---------------------- | ------------------------------------ | ---- | ------- | --------------------------------- |
| `sfx_whoosh.mp3`       | `video-danang/assets/sfx_whoosh.mp3` | 0.45 | `W(t)`  | Scene transition                  |
| `sfx_impact.mp3`       | `video-danang/assets/sfx_impact.mp3` | 0.65 | `I(t)`  | Số đập vào, counter settle        |
| `sfx_pop.mp3`          | `video-danang/assets/sfx_pop.mp3`    | 0.50 | `P(t)`  | Card/box appear                   |
| `sfx_swoosh_light.mp3` | `_shared/sfx/fs_whoosh_light.mp3`    | 0.30 | `SL(t)` | **Text animation slide in (NEW)** |

**6–8 SFX events per video.** Imperative approach — `tl.call(playX, [], t)`.

```js
var sfxWhoosh = new Audio("assets/sfx_whoosh.mp3");
sfxWhoosh.volume = 0.45;
var sfxImpact = new Audio("assets/sfx_impact.mp3");
sfxImpact.volume = 0.65;
var sfxPop = new Audio("assets/sfx_pop.mp3");
sfxPop.volume = 0.5;
var sfxSwooshLight = new Audio("assets/sfx_swoosh_light.mp3");
sfxSwooshLight.volume = 0.3;
function playWhoosh() {
  sfxWhoosh.currentTime = 0;
  sfxWhoosh.play().catch(function () {});
}
function playImpact() {
  sfxImpact.currentTime = 0;
  sfxImpact.play().catch(function () {});
}
function playPop() {
  var s = sfxPop.cloneNode();
  s.volume = 0.45;
  s.play().catch(function () {});
}
function playSwooshLight() {
  var s = sfxSwooshLight.cloneNode();
  s.volume = 0.3;
  s.play().catch(function () {});
}
```

### Nhạc Nền (BGM)

Mỗi video mới **random chọn 1 trong 2 track** trong `_shared/bgm/`:

| File                            | Dùng trong                                  | Ghi chú                                            |
| ------------------------------- | ------------------------------------------- | -------------------------------------------------- |
| `../_shared/bgm/bgm-track1.mp3` | video-danang                                | Track gốc từ video Đà Nẵng · `data-volume="0.276"` |
| `../_shared/bgm/bgm-track2.mp3` | video-symphony5-bao-lon, video-metro-danang | The Pocket — Stan Town · `data-volume="0.2"`       |

**Quy tắc chọn:** Khi viết `index.html` mới, Claude random pick 1 track — không dùng cùng track với video liền trước. Copy file được chọn vào `assets/bgm.mp3` của project đó.

**Volume chuẩn theo track:** bgm-track1 → `0.276` · bgm-track2 (Stan Town) → `0.2`

### Quy Tắc Clip Background (Cập Nhật 2026-06-11)

**Tổng cộng ≤3 footage clips video per video** (hook + body + CTA).

| Vị trí      | ID        | Loại                                              | Yêu cầu                                    |
| ----------- | --------- | ------------------------------------------------- | ------------------------------------------ |
| Hook cover  | `c01`     | Footage video                                     | **≥ 10s**, không trùng source trong 2 tuần |
| Body scenes | —         | **Ảnh tĩnh chủ đạo** + tối đa 2–3 video ngắn < 5s | Ken burn 1.00→1.04, overlay 55-65%         |
| CTA outro   | clip cuối | Footage video                                     | **≥ 8s**, khác source với c01              |

**Transcode footage clips (CRF 18 — chất lượng cao):**

```bash
ffmpeg -i input.mp4 -c:v libx264 -crf 18 -bf 0 -g 30 \
  -movflags +faststart -pix_fmt yuv420p -an output.mp4
```

**Text body**: Luôn trong card/box riêng — không đặt text thẳng lên ảnh/clip.

**Overlay ảnh tĩnh**: `linear-gradient(to bottom, rgba(0,0,0,0.30) 0%, rgba(0,0,0,0.65) 100%)`

**Ken burn**: `gsap.to("#img", { scale: 1.04, duration: sceneDuration, ease: "none" })`

**Clip bị cấm:** `laptop`, `coffee`, `latte`, `ai-code`.

---

## Typography

Font duy nhất cho tất cả video: **Be Vietnam Pro** (đã có sẵn trong `_shared/fonts/`).

| Weight   | Số  | File                            | Dùng cho                             |
| -------- | --- | ------------------------------- | ------------------------------------ |
| Light    | 300 | `BeVietnamPro-Light-*.woff2`    | Sub-text, source tag, chú thích nhỏ  |
| Regular  | 400 | `BeVietnamPro-Regular-*.woff2`  | Body text                            |
| SemiBold | 600 | `BeVietnamPro-SemiBold-*.woff2` | Label, heading phụ                   |
| Black    | 900 | `BeVietnamPro-Black-*.woff2`    | Counter, số liệu lớn, headline chính |

**Khai báo `@font-face` trong mỗi project:** trỏ về `../../../studio/_shared/fonts/` hoặc copy cả folder `_shared/fonts/` vào `fonts/` của project (như video-danang đang làm).

> Không dùng Google Fonts hay font khác — Be Vietnam Pro là chuẩn thương hiệu Bình Phan.

> **BẮT BUỘC:** KHÔNG dùng `font-weight: 700` ở bất kỳ đâu. Be Vietnam Pro chỉ có 4 weights: 300/400/600/900. Weight 700 không khai báo → browser fallback sang system font → tiếng Việt render sai. Heading phụ/button/label → dùng `600`. Số lớn/headline/strong → dùng `900`.

### Kích Thước Text Body — Chuẩn V01/V02

> Áp dụng cho Market Video và Community Video. Không thay đổi tùy tiện.

| Element                   | font-size | font-weight | Ghi chú                                  |
| ------------------------- | --------- | ----------- | ---------------------------------------- |
| `sec-head`                | 40px      | 600         | Heading body scene, gold 0.85 opacity    |
| `block-text`              | 38px      | 600         | Nội dung trong block-row                 |
| `float-num`               | 160px     | 900         | Số lớn trung tâm (7–9%, 50 năm...)       |
| `float-lbl`               | 32px      | 600         | Label dưới float-num, letter-spacing 3px |
| `num-block-text`          | 36px      | 400         | Text trong numbered block                |
| `cmp-num`                 | 68px      | 900         | Số trong compare card                    |
| `cmp-label`               | 22px      | 600         | Zone label trong compare card            |
| `cmp-sub`                 | 22px      | 400         | Sub-text trong compare card              |
| `scene-note`              | 40px      | 400         | Italic note cuối scene                   |
| `source-tag`              | 20px      | 300         | Nguồn dữ liệu, opacity 0.45              |
| `hook-q`                  | 96px      | 900         | Câu hỏi hook                             |
| `hook-ans`                | 200px     | 900         | Câu trả lời hook, gold                   |
| `sig-val` (signal-card)   | 48px      | 900         | Giá trị trong signal card                |
| `sig-lbl` (signal-card)   | 30px      | 400         | Label trong signal card                  |
| `ch-label` (choice-grid)  | 28px      | 900         | Label trong choice card                  |
| `ch-action` (choice-grid) | 32px      | 600         | Action text trong choice card            |

---

## Subtitle Word-by-Word — Quy Tắc Chính Thức (V02)

**BẮT BUỘC áp dụng cho mọi video từ V02 trở đi.**

### CSS

```css
.sub-bar {
  position: absolute;
  bottom: 420px; /* KHÔNG thấp hơn 420px — safe zone bottom = 400px */
  left: 64px;
  right: 64px;
  z-index: 50;
  opacity: 0;
  pointer-events: none;
}
.sub-phrase {
  display: none; /* GSAP set display:flex khi phrase active */
  flex-wrap: nowrap;
  white-space: nowrap; /* KHÔNG xuống dòng */
  gap: 8px;
  align-items: baseline;
}
.sub-w {
  font-size: 44px; /* = 35px gốc × 1.25 */
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  text-shadow:
    0 1px 12px rgba(0, 0, 0, 0.95),
    0 0 24px rgba(0, 0, 0, 0.8);
  /* KHÔNG có background */
}
```

### Quy Tắc Nội Dung

- **≤ 8 từ** mỗi phrase — vừa 1 dòng ở 44px trên canvas 1080px
- Chia phrase theo dấu câu tự nhiên (phẩy, chấm, ý ngắn)
- Phrase cũ biến mất **ngay lập tức** khi phrase mới xuất hiện (không fade)

### JS Pattern

```js
// Fade in sub-bar
tl.fromTo("#sN-sub", { opacity: 0 }, { opacity: 1, duration: 0.25 }, VO_START);

// Show/hide phrases
tl.set("#sN-ph0", { display: "flex" }, PHRASE_TIME);
tl.set("#sN-ph-1", { display: "none" }, PHRASE_TIME); // hide previous

// Word highlight: gold → reset white
tl.set("#sN-ph0-w0", { color: "#ffd166" }, WORD_START);
tl.set("#sN-ph0-w0", { color: "rgba(255,255,255,0.9)" }, NEXT_WORD_START);
```

### Workflow

1. Chạy Whisper lấy word timestamps → lưu `assets/word_timestamps.json`
2. Group words thành phrases ≤8 từ
3. Generate HTML + GSAP set() calls

```bash
~/miniconda3/bin/python3 -c "
from faster_whisper import WhisperModel; import json
model = WhisperModel('small', device='cpu', compute_type='int8')
results = {}
for i in range(1,7):
    segs, _ = model.transcribe(f'assets/vo_s{i}.mp3', language='vi', word_timestamps=True)
    results[f's{i}'] = [{'w':w.word.strip(),'s':round(w.start,3)} for seg in segs for w in (seg.words or [])]
json.dump(results, open('assets/word_timestamps.json','w'), ensure_ascii=False, indent=2)
"
```

---

## Body Component Catalog — V01/V02 Style

### Signal Card (S5 style — 2 cards ngang)

```html
<div class="signal-row">
  <div id="s5-sa" class="signal-card">
    <div class="sig-icon">🏙️</div>
    <div class="sig-val">HN + SG</div>
    <div class="sig-lbl">Nhà đầu tư quay lại</div>
  </div>
  <div id="s5-sb" class="signal-card">...</div>
</div>
```

```css
.signal-row {
  display: flex;
  gap: 24px;
  width: 100%;
  position: relative;
  z-index: 2;
}
.signal-card {
  flex: 1;
  background: rgba(2, 12, 24, 0.78);
  border: 1.5px solid rgba(255, 209, 102, 0.25);
  border-radius: 20px;
  backdrop-filter: blur(16px);
  padding: 36px 24px;
  text-align: center;
  opacity: 0;
}
.sig-icon {
  font-size: 52px;
  line-height: 1;
  margin-bottom: 14px;
}
.sig-val {
  font-size: 48px;
  font-weight: 900;
  color: #ffd166;
  line-height: 1;
  margin-bottom: 8px;
}
.sig-lbl {
  font-size: 30px;
  font-weight: 400;
  color: rgba(200, 220, 240, 0.78);
  line-height: 1.35;
}
```

Animation: `#s5-sa` từ `x:-80`, `#s5-sb` từ `x:+80`, `back.out(1.5)`.

### Choice Grid (S6 style — 4 cards 2×2)

```html
<div class="choice-grid">
  <div id="s6-ch1" class="choice-card">
    <div class="ch-icon">🏠</div>
    <div class="ch-label">Ở Thực</div>
    <div class="ch-action">Vào ngay</div>
  </div>
  <!-- 3 cards nữa -->
</div>
```

```css
.choice-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  width: 100%;
  position: relative;
  z-index: 2;
}
.choice-card {
  background: rgba(2, 12, 24, 0.78);
  border: 1.5px solid rgba(255, 209, 102, 0.25);
  border-radius: 20px;
  backdrop-filter: blur(16px);
  padding: 32px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  text-align: center;
  opacity: 0;
}
.ch-icon {
  font-size: 48px;
  line-height: 1;
}
.ch-label {
  font-size: 28px;
  font-weight: 900;
  text-transform: uppercase;
  color: rgba(220, 235, 250, 0.88);
  line-height: 1.25;
}
.ch-action {
  font-size: 32px;
  font-weight: 600;
  color: #ffd166;
}
```

Animation: row 1 ([ch1,ch2]) và row 2 ([ch3,ch4]) stagger `back.out(1.6)` slide từ `y:60`.

---

## HyperFrames Patterns Hay Dùng

```js
// Data-driven animation — khai báo ANIMS[], loop qua để build timeline
const ANIMS = [
  {
    el: "#title",
    from: { opacity: 0, y: 30 },
    to: { opacity: 1, y: 0 },
    at: 0,
  },
];
ANIMS.forEach((a) => tl.fromTo(a.el, a.from, { ...a.to, duration: 0.4 }, a.at));

// Load VO — dùng synchronous XHR, KHÔNG dùng fetch()
const xhr = new XMLHttpRequest();
xhr.open("GET", "assets/vo_s0.mp3", false);
xhr.send();

// toComp() — convert composition time sang GSAP timeline position
```

Chi tiết: `.agents/skills/hyperframes/SKILL.md`

---

## CTA Scene — Format Mới (Không Có Stats)

**HTML template chuẩn (stats section đã bỏ):**

```html
<div class="morph-bg"></div>
<div class="cta-inner">
  <div class="cta-label">Tóm kết 1 câu ngắn</div>
  <div class="cta-title">Title chính<br /><span>accent</span></div>
  <div class="cta-btn">Button text · Action</div>
  <div class="cta-contact">
    <div class="cta-contact-name">
      Bình Phan <span style="color: #ffd966">IQI</span>
    </div>
    <img class="cta-avatar" src="assets/me-outtro.jpg" alt="Bình Phan" />
  </div>
</div>
```

**CTA button text dynamic:**

- Video **dự án cụ thể** → `"Nhắn Bình"`
- Video **thị trường chung / hạ tầng** → `"Follow để cập nhật"`

**CSS sizes:**

```css
.cta-label {
  font-size: 24px;
  font-weight: 600;
}
.cta-title {
  font-size: 78px;
  font-weight: 900;
  line-height: 1.1;
}
.cta-btn {
  font-size: 32px;
  font-weight: 700;
  border: 2px solid #ffe566;
  /* hapticPulse animation */
}
.cta-contact-name {
  font-size: 34px;
  font-weight: 600;
  color: #ffffff;
}
.cta-avatar {
  width: 336px;
  height: 336px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid rgba(255, 209, 102, 0.6);
  box-shadow: 0 0 40px rgba(255, 209, 102, 0.3);
}
```

> **Không đặt số điện thoại hay địa điểm** — thuật toán bóp tương tác.

---

## Render Settings (Market Video)

| Thông số    | Giá trị                                           |
| ----------- | ------------------------------------------------- |
| HyperFrames | `npm run render -- --sdr --quality high --crf 14` |
| Frame rate  | **60fps**                                         |
| Color space | **SDR, Rec.709**                                  |
| Audio       | **AAC 256 kbps**                                  |
| Resolution  | 1080×1920 (9:16)                                  |
| faststart   | Bắt buộc `-movflags +faststart`                   |

**Thumbnail + concat sau render:**

```bash
# Extract frame hook scene (~2s)
ffmpeg -ss 2 -i renders/video_raw.mp4 -vframes 1 renders/thumbnail.jpg

# Tạo 0.5s clip từ frame
ffmpeg -loop 1 -i renders/thumbnail.jpg \
  -c:v libx264 -t 0.5 -pix_fmt yuv420p -r 60 \
  -vf "scale=1080:1920" -movflags +faststart \
  renders/thumb_clip.mp4

# Concat thumbnail + video
ffmpeg -i renders/thumb_clip.mp4 -i renders/video_raw.mp4 \
  -filter_complex "[0:v][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]" \
  -map "[outv]" -map "[outa]" \
  -c:v libx264 -crf 14 -pix_fmt yuv420p -r 60 \
  -c:a aac -b:a 256k -movflags +faststart \
  renders/video_final.mp4
```

---

## Checklist Trước Khi Render

- [ ] VO 8 segments sync đúng, không gap hay overlap
- [ ] Mọi text tiếng Việt có dấu đầy đủ
- [ ] BGM không lấn VO (-18 dB)
- [ ] CTA: tóm kết + button + avatar Me-outtro (không stats)
- [ ] Duration **60–75s** (market video)
- [ ] Preview đầy đủ 1 lần từ đầu đến cuối

---

## Style Guide — Video Vlog

> Áp dụng cho mọi video vlog (hậu trường, daily, sự kiện). Khác với Market Video ở tông màu, text style và layout.

### Visual

| Yếu tố             | Quy tắc Vlog                                                                                                                                  |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Background overlay | **Bottom gradient only** — không full overlay. `linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.68) 100%)`, height 960px (50% canvas) |
| Neon border        | **Không dùng**                                                                                                                                |
| Hook text màu      | **Vàng #F5D878** — big, centered                                                                                                              |
| Body text màu      | **Trắng #FFFFFF** + `text-shadow: 0 2px 12px rgba(0,0,0,0.6)`                                                                                 |
| Hook position      | `top: 820px`, text-align center, font-size 92px, weight 900                                                                                   |
| Body position      | `bottom: 430px` (safe zone TikTok), font-size 52px, weight 600                                                                                |
| Transition         | Zoom cut — `tl.fromTo("#cap-layer", {scale:1.02}, {scale:1, duration:0.3})` tại mỗi scene start                                               |
| Hook FX            | Fade in mượt + slide up                                                                                                                       |
| Branding           | **Top-right** `top:248px; right:72px` — chỉ hiện ở hook scene và CTA                                                                          |

### CTA Scene

- `#cta` cần `background: rgba(0,0,0,0.55)` để text không chìm trên clip nền sáng
- CTA text-shadow mạnh: `0 2px 20px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.7)`
- CTA background dùng **clip riêng** (không reuse clip đã dùng trong body)

### Audio Vlog

| Thứ     | Quy tắc                                                                                             |
| ------- | --------------------------------------------------------------------------------------------------- |
| BGM     | `-18dB` (`data-volume="0.2"`), chạy đến hết, không fade                                             |
| SFX     | Chỉ ở hook (whoosh→pop) và CTA (pop→whoosh)                                                         |
| Ambient | Clips play muted — không giữ ambient sound từ footage                                               |
| VO sync | Dùng **faster-whisper** (`model=small, language=vi`) để lấy word timestamps → phrase-level captions |

### HyperFrames — Kỹ Thuật Quan Trọng

**1. Clip opacity — dùng GSAP explicit, không chỉ dựa HyperFrames:**

```js
tl.fromTo("#c01", { opacity: 0 }, { opacity: 1, duration: 0.4 }, 0);
tl.to("#c01", { opacity: 0, duration: 0.3 }, endTime);
```

**2. Clip reuse — tạo element riêng, không reuse cùng ID:**

```html
<!-- c04: bong-bay S2 20-30s -->
<video id="c04" ... data-start="20" data-duration="10"></video>
<!-- c04b: bong-bay replay S6 60-66s -->
<video id="c04b" src="assets/c04.mp4" data-start="60" data-duration="6"></video>
```

**3. KHÔNG dùng `loop` + `data-duration` dài trên cùng element** — clip sẽ lặp nhiều lần liên tục (bug visual "clip lặp 3 lần").

**4. KHÔNG dùng imperative media control** — `currentTime`, `.play()` bị HyperFrames chặn (lỗi `imperative_media_control`). Dùng `data-start/data-duration` hoặc element riêng.

**5. Timeline registration bắt buộc trước `tl.play()`:**

```js
window.__timelines = window.__timelines || {};
window.__timelines["composition-id"] = tl;
window.addEventListener("load", () => {
  tl.play();
});
```

**6. Whisper timestamp → captions:**

```bash
~/miniconda3/bin/python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
segs, _ = model.transcribe('assets/vo_s0.mp3', language='vi', word_timestamps=True)
# group words thành phrases → dùng .start/.end cho GSAP timing
"
```

**7. BẮT BUỘC dùng `fromTo()` — KHÔNG dùng `from()` cho element có CSS `opacity: 0`:**

`tl.from(el, {opacity:0})` trên element có CSS `opacity:0` → GSAP đọc target = 0, animate 0→0 → element vô hình suốt. Áp dụng cho mọi element có `.classname { opacity: 0 }` trong stylesheet (sec-head, body-card, block-row, num-block, float-num, story-line, cmp-card, cta-label/title/btn/contact...).

```js
// ❌ SAI — element có CSS opacity:0 → stays invisible
tl.from("#heading", { x: -40, opacity: 0, duration: 0.4 }, t);

// ✓ ĐÚNG — explicit target opacity:1
tl.fromTo(
  "#heading",
  { x: -40, opacity: 0 },
  { x: 0, opacity: 1, duration: 0.4, ease: "power2.out" },
  t,
);

// ✓ Stagger nhiều block-rows / num-blocks
tl.fromTo(
  ["#s1-b1", "#s1-b2", "#s1-b3", "#s1-b4"],
  { x: -48, opacity: 0 },
  { x: 0, opacity: 1, duration: 0.42, stagger: 0.18, ease: "power2.out" },
  t,
);
```

### Hook Style — Vlog

- **Câu hỏi rhetorical** hiệu quả nhất: "Sale chưa có khách thì làm gì?", "Bạn có biết bên trong trông như thế nào không?"
- **Không dùng tiêu đề dạng tin tức** — "SỰ KIỆN BÀN GIAO SỔ ĐỎ" quá formal, không ra vlog
- Hook 2 dòng: dòng 1 lớn (92px weight 900 vàng), dòng 2 nhỏ hơn (50px weight 400 vàng nhạt)

### Duration Vlog

**75–90s** — không cần tròn 90s. Tính từ total VO duration + scene padding.

---

## Projects Hiện Có

| Thư mục                   | Tên                                | Trạng thái        |
| ------------------------- | ---------------------------------- | ----------------- |
| `video-danang`            | Du Lịch Đà Nẵng & Tỷ Suất Cho Thuê | RENDERED ✅       |
| `video-effects-demo`      | 11 Hiệu Ứng Demo                   | CHỜ XÓA — làm lại |
| `video-effects-demo-2`    | 15 Hiệu Ứng Demo — Part 2          | CHỜ XÓA — làm lại |
| `video-symphony5-bao-lon` | Sun Group Báo Lớn — Symphony 5     | Đang làm          |
| `video-effects` (sắp tạo) | 22 Hiệu Ứng Gộp (7+15)             | Chưa tạo          |
