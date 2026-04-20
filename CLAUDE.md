# CLAUDE.md

## Truy Cập Nhanh

- **Content Dashboard:** `open outputs/dashboard.html`
- **Generate infographic:** `python3 scripts/generate-infographic.py --reference <ref> --output <path> --prompt "<prompt>"`

File này cung cấp hướng dẫn cho Claude Code khi làm việc trong repository này.

---

## Đây Là Gì

Đây là một **Content Creation Workspace** — môi trường có cấu trúc để tạo, lập kế hoạch và quản lý nội dung trên mạng xã hội. Claude đóng vai trò đối tác tạo nội dung, hỗ trợ lên ý tưởng, viết nháp, chuyển thể nội dung giữa các nền tảng và giữ sự nhất quán của thương hiệu.

**File này (CLAUDE.md) là nền tảng của workspace.** Nó được nạp tự động ở đầu mỗi session và là nguồn sự thật chính để Claude hiểu cách hoạt động trong repo này.

---

## Bạn Là Ai

> **Điền thông tin của bạn vào đây.** Sau khi chạy `/init-context`, section này sẽ được tự động điền từ dữ liệu scrape. Hoặc tự điền thủ công và xem `context/profile.md` để có đầy đủ hơn.

- **Tên:** [TÊN ĐẦY ĐỦ]
- **Tên công khai:** [TÊN THƯƠNG HIỆU CÔNG KHAI — ví dụ: "Nguyễn Nam - AI Expert"]
- **Khu vực:** [THÀNH PHỐ, QUỐC GIA]
- **Vai trò:** [VAI TRÒ — ví dụ: Founder, Creator, Educator, Consultant]
- **Thương hiệu hướng ra công chúng:** [BRAND_NAME]
- **Thương hiệu công ty:** [COMPANY_NAME]
- **Bối cảnh:** [MÔ TẢ NGẮN — bạn làm gì, cho ai, tại sao — 2-3 câu]
- **Sứ mệnh:** [SỨ MỆNH của bạn — 1 câu rõ ràng]

### Kênh Chính Thức

- Website: [WEBSITE_URL]
- Website công ty: [COMPANY_URL]
- TikTok: [TIKTOK_URL]
- Facebook: [FACEBOOK_URL]
- YouTube: [YOUTUBE_URL]

---

## Quan Hệ Giữa Claude Và User

Claude hoạt động như một **đối tác tạo nội dung** với quyền truy cập vào thư mục, context, command và output trong workspace. Mối quan hệ là:

- **Bạn:** quyết định định hướng nội dung, cung cấp bối cảnh thô, duyệt đầu ra cuối cùng
- **Claude:** viết nháp, đề xuất ý tưởng, điều chỉnh nội dung cho từng nền tảng, giữ nhất quán giọng thương hiệu và tổ chức workflow nội dung

Claude nên luôn tự định hướng bằng `/prime` ở đầu session, sau đó hành động với nhận thức đầy đủ về thương hiệu, giọng điệu, tệp khán giả và mục tiêu chiến lược của bạn.

### Hướng Dẫn Về Giọng Điệu

- **Gần gũi và trực diện** — viết như đang nói chuyện với một người thông minh, không viết như đang phát biểu cho đám đông
- **Thật và thực chiến** — chia sẻ con số thật, khó khăn thật, bài học thật
- **Thực dụng hơn lý thuyết** — ưu tiên nội dung hành động được
- **Tự tin nhưng không giáo điều** — nói rõ điều gì đang hiệu quả và điều gì chưa
- **Không văn phong doanh nghiệp sáo rỗng** — tránh buzzword, jargon và filler
- **Cách xưng hô mặc định:** "mình", "bạn", "các bạn", "bên mình", "công ty mình"

---

## Cấu Trúc Workspace

```
.
├── CLAUDE.md              # File này — context cốt lõi, luôn được nạp
├── .claude/
│   ├── commands/          # Slash commands: /init-context, /prime, /create-10-posts, /create-plan, /implement
│   └── skills/            # Skills: viral-replication, content-ideation, carousel-creation, gmail-label
├── .env                   # API keys (Apify, Kie.ai) — không commit
├── context/               # Toàn bộ bối cảnh về bạn
│   ├── profile.md         #   Bạn là ai (tên, link, giọng điệu, cá tính)
│   ├── business.md        #   Bạn đang làm gì (công ty, sản phẩm, audience)
│   ├── strategy.md        #   Bạn đang đi đâu (mục tiêu, ưu tiên)
│   ├── metrics.md         #   Các con số hiện tại
│   ├── images/            #   Ảnh cá nhân cho post
│   └── data/              #   Dữ liệu scrape từ social
├── posts/                 # Nội dung cuối cùng — mỗi post một thư mục
├── outputs/               # File làm việc, dashboard, bản nháp
├── reference/             # Style guide, visual refs, ví dụ copywriting
├── scripts/               # Tự động hóa (dashboard builder, carousel generator)
└── plans/                 # Kế hoạch triển khai
```

**Các thư mục chính:**

| Thư mục      | Mục đích                                                                                                         |
| ------------ | ---------------------------------------------------------------------------------------------------------------- |
| `context/`   | **Toàn bộ thông tin về bạn** — profile, business, strategy, metrics, ảnh, dữ liệu scrape. Được đọc bởi `/prime`. |
| `posts/`     | **Nội dung cuối cùng** — mỗi post một thư mục, chứa ảnh + text + tài liệu gốc nếu có.                            |
| `reference/` | Tài liệu tham chiếu về visual style, copywriting và ví dụ nội dung.                                              |
| `outputs/`   | File làm việc, dashboard, bản nháp, idea bank, research.                                                         |
| `scripts/`   | Script dựng dashboard, tạo carousel và các phần tự động hóa.                                                     |
| `plans/`     | Kế hoạch nội dung và kế hoạch triển khai. Được tạo bởi `/create-plan`.                                           |

---

## Các Command

### /init-context [URL và/hoặc text]

**Mục đích:** Xây lại toàn bộ context của workspace từ đầu.

Command này nhận URL social, website và/hoặc text tự do. Nó sẽ scrape mọi nguồn phù hợp qua Apify, phân tích dữ liệu, tạo các file context và cập nhật `CLAUDE.md`.

Ví dụ: `/init-context https://www.linkedin.com/in/username/ https://www.youtube.com/@Channel Họ đang xây một B2B SaaS cho ngành tuyển dụng`

### /prime

**Mục đích:** Khởi tạo một session mới với đầy đủ nhận thức về context.

Hãy chạy command này ở đầu mỗi session. Claude sẽ đọc toàn bộ context và xác nhận đã sẵn sàng.

### /create-10-posts

**Mục đích:** Tạo một batch 10 nội dung sẵn sàng xuất bản trong một lần chạy.

Batch này tạo ra:

- **Theo phương pháp:** 5 viral replication + 3 trend surfing + 2 pain points
- **Theo định dạng:** 4 ảnh cá nhân + 4 AI infographic + 2 carousel
- **Mọi nội dung đều có visual** — không có bài chỉ có text
- Tất cả nội dung đều phải tự đứng được một mình
- Có kiểm soát độ đa dạng về chủ đề, hook, visual và tông giọng

### /create-plan [request]

**Mục đích:** Tạo một kế hoạch triển khai chi tiết trước khi bắt đầu thay đổi.

Ví dụ: `/create-plan chuỗi nội dung hàng tuần về các sai lầm khi ứng dụng AI cho doanh nghiệp`

### /implement [plan-path]

**Mục đích:** Thực thi một kế hoạch đã được tạo bởi `/create-plan`.

Ví dụ: `/implement plans/2026-03-05-linkedin-series.md`

---

## Nền Tảng Và Cách Tiếp Cận

| Nền tảng  | Mức ưu tiên | Tệp khán giả                                           | Trọng tâm nội dung                                                                     |
| --------- | ----------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| Facebook  | Cao         | Người đi làm, founder, operator, marketer tại Việt Nam | Chia sẻ thực chiến, quan điểm, góc nhìn founder, nội dung viết có khả năng chuyển đổi  |
| TikTok    | Cao         | Tệp rộng quan tâm tới AI, năng suất, công cụ           | Demo nhanh, hook mạnh, use case thật, agentic workflow ngắn gọn                        |
| YouTube   | Cao         | Người muốn hiểu sâu và ứng dụng bài bản                | Tutorial agentic workflow, breakdown multi-agent system, case study, authority content |
| Instagram | Thấp        | Tệp phụ                                                | Repurpose visual, reels, carousel ngắn                                                 |
| LinkedIn  | Thấp        | Tệp chuyên môn phụ                                     | Authority B2B và narrative chuyên môn nếu cần sau này                                  |

---

## Chỉ Dẫn Quan Trọng: Luôn Duy Trì File Này

**Bất cứ khi nào Claude thay đổi workspace, Claude PHẢI tự hỏi liệu `CLAUDE.md` có cần cập nhật hay không.**

Sau mỗi thay đổi — thêm command, script, workflow hoặc chỉnh cấu trúc — hãy tự hỏi:

1. Does this change add new functionality users need to know about?
2. Does it modify the workspace structure documented above?
3. Should a new command be listed?
4. Does context/ need new files to capture this?

Nếu câu trả lời là có cho bất kỳ mục nào, hãy cập nhật phần liên quan. File này luôn phải phản ánh trạng thái thực của workspace để các session sau có context chính xác.

---

## Workflow Chính: Viral Replication

Chiến lược nội dung cốt lõi hiện tại là **viral replication** — tìm những nội dung đã chứng minh hiệu quả rồi tái tạo phần đóng gói, đồng thời thay thế phần substance bằng góc nhìn và chủ đề của bạn.

Quy trình đầy đủ nằm trong `.claude/skills/viral-replication/SKILL.md`. Tóm tắt:

1. **Tìm** một nội dung viral trong niche
2. **Lấy phần đóng gói** — hook, cấu trúc thân bài, bố cục hình ảnh, cơ chế CTA
3. **Thay phần substance** — đổi chủ đề sang của bạn, áp dụng visual style và giọng thương hiệu của bạn
4. **Viết theo tinh thần Adam Robinson** — thô, đời, mang cảm giác người thật
5. **Tạo visual** theo layout gốc nhưng trong style thương hiệu
6. **Lưu** vào `posts/NNN-slug/` cùng toàn bộ asset
7. **Dựng lại dashboard** bằng `python3 scripts/build-dashboard.py`

### Visual Style

> **Hãy chỉnh màu sắc và style để khớp với thương hiệu của bạn. Thêm ảnh tham chiếu vào `reference/`.**

Mọi infographic **bắt buộc** phải dùng một hệ style nhất quán. Mặc định template đang dùng:

- Nền cream sáng `#F5F3EE` với dot grid nhẹ
- Accent xanh lime `#C8E64A`
- Heading sans-serif đậm màu đen, body text xám
- Icon line-art đơn giản, badge số theo màu accent
- Banner dưới màu tối `#1A1A1A`
- Cần thêm 3 ảnh tham chiếu `reference/infographic-ref-*.jpeg`

### Tạo Ảnh — Cách Làm Bắt Buộc

**QUAN TRỌNG: Luôn duyệt nội dung với user TRƯỚC KHI generate ảnh.** Tạo ảnh tốn API call và thời gian — nếu nội dung không dùng được thì lãng phí. Quy trình bắt buộc:

1. Viết toàn bộ text content cho tất cả post
2. Trình bày cho user duyệt (tiêu đề, hook, nội dung chính, mô tả visual)
3. Chỉ sau khi user xác nhận mới generate ảnh/carousel

**Luôn dùng Kie.ai API (model: `nano-banana-pro`) với tham số `reference_image`.**

- Resize ảnh tham chiếu về 512px, encode base64 rồi truyền vào `reference_image`
- Cách này giúp giữ brand consistency tự động
- Luân phiên ảnh tham chiếu để đa dạng bố cục:
  - `infographic-ref-1.jpeg` — bố cục tròn/radial
  - `infographic-ref-2.jpeg` — các thành phần xoay quanh headline
  - `infographic-ref-3.jpeg` — flow dọc
- **Prompt PHẢI chứa tiếng Việt đầy đủ dấu** — KHÔNG gửi prompt không dấu rồi để AI tự đoán. Thêm "CRITICAL: render Vietnamese diacritics exactly as provided" vào cuối prompt.
- Sau khi generate, KIỂM TRA text trên ảnh. Nếu sai dấu tiếng Việt → regenerate hoặc dùng Pillow để sửa text overlay.
- Không dùng Pillow đơn lẻ để tạo infographic (Kie.ai + Pillow hybrid OK)
- Không dùng nền tối, màu neon hoặc palette lệch brand
- Kiểm tra các post đã có trước khi tạo để tránh 2 infographic liền nhau cùng layout
- Với post dùng ảnh cá nhân: chọn từ `context/images/` sao cho hợp vibe bài, sau đó **BẮT BUỘC** chạy `add-photo-overlay.py` để thêm text hook lên ảnh (xem hướng dẫn bên dưới)

**Ảnh cá nhân — quy trình bắt buộc:**

```bash
python3 scripts/add-photo-overlay.py \
  --photo context/images/PHOTO.jpg \
  --text "Hook text ngắn gọn, tối đa ~12 từ" \
  --highlight "TỪ KHÓA" "CON SỐ" \
  --output posts/NNN-slug/image.png \
  --position bottom   # bottom | top | center
```

- `--text`: lấy từ hook đầu bài (dòng 1-2), đủ ngắn để đọc khi lướt
- `--highlight`: số liệu và từ nhấn mạnh sẽ hiện màu lime `#C8E64A`
- `--position`: `bottom` (mặc định), `top` cho ảnh cảnh quan, `center` cho ảnh chân dung đơn
- Không overlay lên mặt người — chọn position tránh vùng mặt

Xem `.claude/skills/viral-replication/SKILL.md` để lấy code API và prompt template đầy đủ.

### Lên Ý Tưởng Nội Dung

Ý tưởng được tạo theo 3 hướng bổ trợ lẫn nhau:

1. **Viral Replication Ideas** — tìm các bài đã chứng minh hiệu quả và đề xuất cách lấy phần đóng gói
2. **Trend Surfing Ideas** — bám các thứ đang nổi lên ngay lúc này trong niche
3. **Audience Pain Point Ideas** — đào sâu vấn đề thật của khán giả và tạo nội dung giúp giải quyết

Quy trình đầy đủ nằm trong `.claude/skills/content-ideation/SKILL.md`. Output lưu vào `outputs/YYYY-MM-DD-content-ideas.md`.

### Tạo Carousel

Carousel hiện được tạo dưới dạng PDF. Quy trình đầy đủ nằm trong `.claude/skills/carousel-creation/SKILL.md`.

1. **Viết nội dung** — tiêu đề + 5-9 ý chính được đánh số, mỗi ý có heading, subtitle, takeaway
2. **Tạo JSON** — dùng key `slides` với các object chứa `number`, `heading`, `subtitle`, `takeaway`
3. **Tạo PDF** — `python3 scripts/generate-carousel.py --json content.json --output posts/NNN-slug/carousel.pdf`
4. **Style** — chỉnh màu sắc và branding trong `scripts/generate-carousel.py`
5. **Mỗi slide nên có minh họa khác nhau**
6. **Tham chiếu carousel** — thêm slide ví dụ vào `reference/carousel-ref/`
7. **Lưu** vào `posts/NNN-slug/` với `carousel.pdf` + `post.md`
8. **Slide PNGs** sẽ được lưu tự động vào `carousel-slides/` để preview trên dashboard

### Phong Cách Copywriting (Adam Robinson)

- Giọng viết mang tính hội thoại, suy nghĩ thành tiếng, có ngoặc chen ý
- Cố ý không quá bóng bẩy, có mảnh câu, có chữ in hoa để nhấn
- Có số liệu cụ thể, có tự trào, có cảm giác người thật
- Xem `reference/adam-robinson-writing-style.md` để đọc hướng dẫn đầy đủ
- Xem `reference/adam-robinson-top-posts.md` để xem các ví dụ thật

---

## Quy Ước Lưu Trữ Post

Each post lives in `posts/NNN-slug/` where NNN is a zero-padded number:

```
posts/001-example-post/
├── post.md              # Metadata + copy-paste ready text
├── image.png            # Final image (personal photo or AI infographic)
├── carousel.pdf         # Carousel PDF (for carousel posts)
├── carousel-slides/     # Auto-generated slide PNGs (for dashboard preview)
├── content.json         # Carousel content JSON (for carousel posts)
├── original.md          # Original viral post reference
└── original-image.jpg   # Original image for comparison
```

**Mỗi post bắt buộc phải có visual** — hoặc `image.png`, hoặc `carousel.pdf` + `carousel-slides/`. Không có bài chỉ có text.

### Chuẩn Format post.md

**1 phiên bản duy nhất** — không tạo 3 phiên bản riêng cho từng nền tảng. Giữ phiên bản đầy đủ nhất, dùng cho tất cả.

**Post text phải là plain text copy-paste ready** — người dùng copy thẳng vào Facebook/TikTok/YouTube mà không cần chỉnh sửa:

- KHÔNG dùng `**bold**` trong post text → thay bằng VIẾT HOA để nhấn mạnh
- KHÔNG dùng `##` heading trong post text → dùng dòng trắng phân đoạn
- KHÔNG dùng backtick hay ký tự markdown khác trong post text
- Dấu `-` đầu dòng cho list là OK
- Hashtag để cuối bài, dòng riêng
- Metadata (ngày đăng, phương pháp, visual...) vẫn dùng markdown bình thường

Template chuẩn:

```markdown
# Bài NNN: Tiêu Đề

**Ngày đăng:** DD/MM/YYYY — Slot sáng/chiều
**Phương pháp:** Viral Replication / Trend Surfing / Pain Point
**Visual:** Ảnh cá nhân / AI Infographic (ref-N layout)
**Platform:** Facebook, crosspost TikTok + YouTube

---

## Post Text

[Nội dung plain text, copy-paste được thẳng vào mạng xã hội]

---

## Image Notes

[Mô tả visual, lệnh generate ảnh nếu cần]
```

Sau khi thêm hoặc cập nhật post, chạy `python3 scripts/build-dashboard.py` để dựng lại dashboard HTML ở `outputs/dashboard.html`.

---

## Workflow Theo Session

1. **Bắt đầu**: chạy `/prime` để nạp context
2. **Làm việc**: yêu cầu Claude viết nháp, brainstorm hoặc chỉnh nội dung
3. **Lập kế hoạch**: dùng `/create-plan` cho campaign hoặc thay đổi workspace
4. **Triển khai**: dùng `/implement` để thực hiện kế hoạch
5. **Bảo trì**: Claude cập nhật `CLAUDE.md` và `context/` khi workspace thay đổi

---

## Tools & APIs

| Công cụ       | Mục đích                                                              | Cấu hình                      |
| ------------- | --------------------------------------------------------------------- | ----------------------------- |
| **Apify**     | Scrape dữ liệu social media                                           | `APIFY_API_KEY` trong `.env`  |
| **Kie.ai**    | Tạo ảnh bằng model `nano-banana-pro`, bắt buộc dùng `reference_image` | `KIE_AI_API_KEY` trong `.env` |
| **Gmail MCP** | Đọc, phân loại, gán nhãn email tự động. Xem skill `gmail-label`       | Gmail OAuth qua MCP server    |

---

## Skills Reference

Skill trong workspace (`/.claude/skills/`) được load tự động. Nếu bạn muốn cài thêm skill ở cấp user (dùng được ở mọi project), đặt vào `~/.claude/skills/` với cùng cấu trúc.

Khi cần dùng skill nào, đọc file SKILL tương ứng trước khi thực hiện.

---

## Project Rules

- **Luôn đọc SKILL.md tương ứng TRƯỚC khi thực hiện task** — mỗi skill có quy trình, template và constraint riêng. Không được bỏ qua bước này.

---

## Ghi Chú

- Giữ context đủ dùng nhưng không phình to không cần thiết
- Kế hoạch được lưu trong `plans/` với tên file có ngày để giữ lịch sử
- Output được tổ chức theo nền tảng/loại trong `outputs/`
- Tài liệu tham chiếu nằm trong `reference/` để tái sử dụng
- Nội dung luôn phải phản ánh giọng thật của bạn, không được generic hoặc corporate
- `context/data/` chứa dữ liệu scrape từ social, cần re-scrape định kỳ để giữ mới
- Chỉ `slug` và tên thư mục dùng không dấu; mọi text hiển thị trong `post.md`, `content.json`, carousel và infographic phải giữ đầy đủ tiếng Việt có dấu
