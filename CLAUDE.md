# CLAUDE.md

## Truy Cập Nhanh

- **Content Dashboard:** `open outputs/dashboard.html`
- **Generate infographic:** `python3 scripts/generate-infographic.py --reference <ref> --output <path> --prompt "<prompt>"`
- **Research dự án:** `python3 scripts/research_bot.py "<query>" --output context/projects/<slug>.md`

File này cung cấp hướng dẫn cho Claude Code khi làm việc trong repository này.

---

## Đây Là Gì

Đây là một **Content Creation Workspace** — môi trường có cấu trúc để tạo, lập kế hoạch và quản lý nội dung trên mạng xã hội. Claude đóng vai trò đối tác tạo nội dung, hỗ trợ lên ý tưởng, viết nháp, chuyển thể nội dung giữa các nền tảng và giữ sự nhất quán của thương hiệu.

**File này (CLAUDE.md) là nền tảng của workspace.** Nó được nạp tự động ở đầu mỗi session và là nguồn sự thật chính để Claude hiểu cách hoạt động trong repo này.

---

## Bạn Là Ai

> _Auto-generated từ TikTok scrape — 2026-05-07. Xem `context/profile.md` để đầy đủ hơn._

- **Tên:** Bình Phan
- **Tên công khai:** Bình Phan – BĐS Đà Nẵng
- **Khu vực:** Đà Nẵng, Việt Nam
- **Vai trò:** Chuyên viên môi giới BĐS / Sales IQI Đà Nẵng
- **Thương hiệu hướng ra công chúng:** Bình Phan BĐS
- **Thương hiệu công ty:** IQI Đà Nẵng
- **Bối cảnh:** 10 năm kinh nghiệm trong ngành bất động sản. Hiện chuyên phân phối các dự án Vinhomes tại Đà Nẵng (Vinhomes Hải Vân Bay, Vinhomes Lang Van). Đang xây dựng personal brand trên TikTok và Facebook để tiếp cận nhà đầu tư và người mua nhà.
- **Sứ mệnh:** Giúp khách hàng đưa ra quyết định đầu tư BĐS đúng đắn bằng thông tin minh bạch và góc nhìn 10 năm thực chiến.

### Kênh Chính Thức

- Website: TBD
- Website công ty: TBD (IQI)
- TikTok: https://www.tiktok.com/@binh_phan_bds
- Facebook: https://www.facebook.com/binhvp
- YouTube: TBD

---

## Quan Hệ Giữa Claude Và User

Claude hoạt động như một **đối tác tạo nội dung** với quyền truy cập vào thư mục, context, command và output trong workspace. Mối quan hệ là:

- **Bạn:** quyết định định hướng nội dung, cung cấp bối cảnh thô, duyệt đầu ra cuối cùng
- **Claude:** viết nháp, đề xuất ý tưởng, điều chỉnh nội dung cho từng nền tảng, giữ nhất quán giọng thương hiệu và tổ chức workflow nội dung

Claude nên luôn tự định hướng bằng `/prime` ở đầu session, sau đó hành động với nhận thức đầy đủ về thương hiệu, giọng điệu, tệp khán giả và mục tiêu chiến lược của bạn.

### Hướng Dẫn Về Giọng Điệu

Giọng của người đã đi qua đủ va chạm trong nghề — nói bằng trải nghiệm, không nói kiểu quảng cáo. Ưu tiên "người thật việc thật" hơn "người viết hay".

**Tông:** Trực diện, storytelling, cảm xúc đến từ trải nghiệm thật, có chiều sâu nhưng không triết lý nặng tay.

**Cách xưng hô:** "mình" (kể chuyện cá nhân) — "bạn" (kéo người đọc vào) — "anh em" (gần gũi, đồng hành) — "Bình" (nhấn mạnh cá nhân). Không xưng "tôi".

**Cấu trúc ưu tiên:**

- Quan sát → Vấn đề → Hiểu ra → Bài học
- Chuyện cũ → Va chạm → Thay đổi → Kết luận
- Điều tưởng đúng → Điều thật sự đúng → Vì sao

**Mở bài:** Lát cắt thật — tình huống, va chạm, quan sát cụ thể. Không mở bằng lý thuyết.
**Kết bài:** Nhận định cụ thể và gọn — không kết bằng câu tổng quát chung chung.

**Tuyệt đối tránh:** Sales áp lực — giật tít quá đà — hứa lợi nhuận quá lố — giọng corporate — slogan rỗng — lập luận nghe đúng nhưng không có đời sống — viết như PR doanh nghiệp.

Xem chi tiết đầy đủ tại `context/voice-analysis.md`.

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
│   ├── career-history.md  #   10 năm sự nghiệp + kho chuyện thật cho content
│   ├── voice-analysis.md  #   Bộ quy tắc giọng viết đầy đủ
│   ├── icp.md             #   Chân dung khách hàng mục tiêu
│   ├── danang-market.md   #   Thị trường Đà Nẵng: hạ tầng, du lịch, tỷ suất cho thuê, lãi suất — cập nhật liên tục
│   ├── images/            #   Ảnh cá nhân cho post
│   ├── projects/          #   Tài liệu từng dự án BĐS:
│   │   ├── sun-symphony-residence5.md
│   │   ├── vinhomes-hai-van-bay.md
│   │   └── fours-tower.md
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
- **Theo định dạng:** 5 ảnh cá nhân + 2 AI infographic + 3 carousel
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

| Nền tảng     | Mức ưu tiên | Tệp khán giả                                     | Trọng tâm nội dung                                                                       |
| ------------ | ----------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Facebook BMN | Cao         | Khách hàng Đà Nẵng, nhà đầu tư, người quen biết  | Tất cả loại nội dung — cá nhân, dự án, thị trường                                        |
| Facebook IQI | Cao         | Nhà đầu tư, người mua BĐS cao cấp                | **Chỉ Dự án + Phân Tích Thị Trường** — không đăng bài cá nhân                            |
| TikTok       | Cao         | Nhà đầu tư, người mua nhà, tệp rộng quan tâm BĐS | **Chỉ đăng Carousel** — hook mạnh, storytelling ngắn gọn                                 |
| Instagram    | Trung bình  | Tệp phụ, lifestyle                               | **Không đăng nội dung về dự án cụ thể** — chỉ storytelling, kinh nghiệm nghề, thị trường |
| Threads      | Trung bình  | Tệp phụ                                          | **Không đăng nội dung về dự án cụ thể** — chỉ storytelling, kinh nghiệm nghề, thị trường |
| YouTube      | Thấp        | TBD — chưa có kênh                               | Tutorial/case study BĐS nếu mở rộng sau này                                              |

### Quy Tắc Nền Tảng (BẮT BUỘC)

- **TikTok:** Chỉ đăng bài định dạng **Carousel**. Không đăng ảnh đơn hoặc infographic.
- **Instagram & Threads:** Không đăng bài về dự án BĐS cụ thể (Symphony, Vinhomes HVB, FourS...). Chỉ đăng nội dung chung: storytelling cá nhân, kinh nghiệm nghề, góc nhìn thị trường, pain points.
- **Facebook BMN (Bình Mê Nhà):** Đăng tất cả loại nội dung — cá nhân, dự án, thị trường.
- **Facebook IQI (Bình Phan IQI):** Chỉ đăng **Dự án** và **Phân Tích Thị Trường**. Không đăng bài cá nhân/storytelling.

### Lịch Đăng Chuẩn — BMN 7 Bài / IQI 4 Bài / Ngày

| Giờ cơ sở | #   | Định dạng   | Chủ đề     | BMN | IQI | TikTok | IG  | Threads |
| --------- | --- | ----------- | ---------- | :-: | :-: | :----: | :-: | :-----: |
| 6:30      | 1   | Ảnh cá nhân | Cá nhân    | ✅  | ❌  |   —    | ✅  |   ✅    |
| 8:30      | 2   | Carousel    | Dự án      | ✅  | ✅  |   ✅   |  —  |    —    |
| 11:00     | 3   | Infographic | Thị Trường | ✅  | ✅  |   —    | ✅  |   ✅    |
| 13:00     | 4   | Ảnh cá nhân | Dự án      | ✅  | ✅  |   —    |  —  |    —    |
| 16:00     | 5   | Carousel    | Cá nhân    | ✅  | ❌  |   ✅   |  —  |    —    |
| 19:00     | 6   | Ảnh cá nhân | Cá nhân    | ✅  | ❌  |   —    | ✅  |   ✅    |
| 21:00     | 7   | Infographic | Dự án      | ✅  | ✅  |   —    |  —  |    —    |

**Tổng mỗi ngày:** BMN 7 · IQI 4 · TikTok 2 · Instagram 3 · Threads 3

**Randomization ±180 giây:** Mỗi lần đăng, lệch ngẫu nhiên −180 đến +180 giây so với giờ cơ sở. Mỗi ngày lệch khác nhau để tránh thuật toán nhận ra pattern tự động.

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

### Visual Style — Infographic

Mọi infographic **bắt buộc** dùng tiếng Việt đầy đủ dấu. Chọn 1 trong 3 layout mẫu bên dưới tùy nội dung:

| Mẫu       | File                          | Layout                                                                                                       | Khi nào dùng                                                                     |
| --------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| **Ref 1** | `reference/inforgraphic1.jpg` | Numbered facts, nền xanh nhạt, illustration trung tâm, các khối thông tin tản xung quanh có badge số (#1–#N) | Danh sách "X điều/thông tin cần biết", educational facts, nhiều data points rời  |
| **Ref 2** | `reference/inforgraphic2.jpg` | Ranking bar chart, header tím/navy, thanh ngang màu cam, flat character illustration góc phải                | So sánh, ranking, thị trường nhiều đối tượng, "X so với Y", tỷ suất theo khu vực |
| **Ref 3** | `reference/inforgraphic3.jpg` | Process flow 2 cột, nền xanh periwinkle, cột trái (biểu đồ/số liệu) + cột phải (flow mũi tên step-by-step)   | Quy trình, "cách hoạt động", timeline, hành trình mua BĐS, các bước đầu tư       |

**Elements bắt buộc trong mọi infographic:**

- **Toàn bộ text phải là tiếng Việt có dấu** — tiêu đề, label, số liệu, chú thích
- **Số liệu lớn** làm neo thị giác — %, tỷ đồng, km, m², năm
- **Flat design illustrations** phù hợp chủ đề BĐS Đà Nẵng: buildings, căn hộ, bản đồ, cảnh quan
- **Typography hierarchy rõ ràng:** Tiêu đề lớn → số liệu nổi → body text nhỏ
- Không để 2 infographic liền nhau cùng layout mẫu trong một batch

### Chọn Ảnh Theo Chủ Đề Bài

**Quy tắc ưu tiên ảnh:**

| Loại nội dung                                          | Ảnh dùng           | Nguồn                                  |
| ------------------------------------------------------ | ------------------ | -------------------------------------- |
| Bài về dự án cụ thể (Symphony, Vinhomes HVB, FourS...) | Ảnh của dự án đó   | `context/images/projects/<tên-dự-án>/` |
| Bài storytelling / kinh nghiệm cá nhân                 | Ảnh chân dung Bình | `context/images/`                      |
| Bài phân tích thị trường / số liệu                     | AI Infographic     | Kie.ai                                 |
| Carousel                                               | Ảnh chân dung Bình | `context/images/`                      |

- **Bài về Sun Symphony** → dùng ảnh từ `context/images/projects/sun-symphony/`
- **Bài về Vinhomes Hải Vân Bay** → dùng ảnh từ `context/images/projects/vinhomes-hai-van-bay/`
- **Bài về FourS Tower** → dùng ảnh từ `context/images/projects/fours-tower/`
- Nếu thư mục dự án chưa có ảnh → dùng ảnh cá nhân Bình làm fallback, ghi chú trong `post.md`

---

### Tạo Ảnh — Cách Làm Bắt Buộc

**QUAN TRỌNG: Luôn duyệt nội dung với user TRƯỚC KHI generate ảnh.** Tạo ảnh tốn API call và thời gian — nếu nội dung không dùng được thì lãng phí. Quy trình bắt buộc:

1. Viết toàn bộ text content cho tất cả post
2. Trình bày cho user duyệt (tiêu đề, hook, nội dung chính, mô tả visual)
3. Chỉ sau khi user xác nhận mới generate ảnh/carousel

**Luôn dùng Kie.ai API (model: `nano-banana-pro`) với tham số `reference_image`.**

- Resize ảnh tham chiếu về 512px, encode base64 rồi truyền vào `reference_image`
- Cách này giúp giữ brand consistency tự động
- Luân phiên ảnh tham chiếu theo loại nội dung:
  - `reference/inforgraphic1.jpg` — **Numbered facts, nền xanh nhạt** — danh sách "X điều cần biết", nhiều data points rời, educational
  - `reference/inforgraphic2.jpg` — **Ranking bar chart, header tím** — so sánh, ranking thị trường, tỷ suất theo khu vực
  - `reference/inforgraphic3.jpg` — **Process flow 2 cột, nền periwinkle** — quy trình, timeline, các bước đầu tư, hành trình mua BĐS
- **Output PHẢI là tiếng Việt có dấu đầy đủ** — tiêu đề, label, số liệu, chú thích đều phải tiếng Việt
- **Prompt PHẢI chứa tiếng Việt đầy đủ dấu** — KHÔNG gửi prompt không dấu. Thêm "CRITICAL: render Vietnamese diacritics exactly as provided, all text must be in Vietnamese" vào cuối prompt
- Sau khi generate, KIỂM TRA text trên ảnh. Nếu sai dấu tiếng Việt hoặc có chữ tiếng Anh không mong muốn → regenerate hoặc dùng Pillow để sửa text overlay
- Không dùng Pillow đơn lẻ để tạo infographic (Kie.ai + Pillow hybrid OK)
- Kiểm tra các post đã có trước khi tạo để tránh 2 infographic liền nhau cùng layout mẫu
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

Carousel dưới dạng PDF — **portrait photo + gradient overlay style** theo mẫu q1-q6: ảnh chân dung Bình (mặt hiện rõ ở trên) + gradient tối dần xuống + số lime to + heading trắng + body text đầy đủ. Canvas **1080×1620px** (2:3). Chi tiết style trong `reference/carousel-ref/carousel-style-analysis.md`.

**Quy trình:**

1. **Viết nội dung** — tiêu đề + 4-6 ý chính, mỗi ý có heading, subtitle (hỗ trợ `• ` bullet), takeaway
2. **Tạo JSON** — format chuẩn bên dưới
3. **Ảnh nền** — dùng ảnh chân dung đứng của Bình, khuyến nghị `IMG_7928.jpg`
4. **Tạo PDF:**

```bash
python3 scripts/generate-carousel.py \
  --json posts/NNN-slug/content.json \
  --output posts/NNN-slug/carousel.pdf \
  --photo context/images/IMG_7928.jpg
```

5. **Lưu** — `carousel.pdf` + `carousel-slides/` tự động tạo + `post.md`

**JSON format chuẩn:**

```json
{
  "title": "Tiêu đề cover",
  "slides": [
    { "number": "00", "subtitle": "Cover subtitle" },
    {
      "number": "01",
      "label": "CATEGORY (tùy chọn)",
      "heading": "Heading ngắn",
      "subtitle": "Body text. **Highlight lime** với dấu sao.\n\n• Bullet point\n• Bullet point",
      "takeaway": "Câu kết in lime."
    },
    { "number": "", "heading": "CTA text", "subtitle": "CTA sub" }
  ]
}
```

- `"00"` → cover subtitle (không tạo content slide)
- `""` → CTA slide cuối
- `label` → category label ALL CAPS lime, optional
- `**word**` → inline lime highlight trong subtitle/takeaway
- `• ` đầu dòng → bullet với indent tự động

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

| Công cụ        | Mục đích                                                              | Cấu hình                          |
| -------------- | --------------------------------------------------------------------- | --------------------------------- |
| **Apify**      | Scrape dữ liệu social media                                           | `APIFY_API_KEY` trong `.env`      |
| **Kie.ai**     | Tạo ảnh bằng model `nano-banana-pro`, bắt buộc dùng `reference_image` | `KIE_AI_API_KEY` trong `.env`     |
| **Perplexity** | Research thời gian thực qua `research_bot.py`, model `sonar-pro`      | `PERPLEXITY_API_KEY` trong `.env` |
| **Gmail MCP**  | Đọc, phân loại, gán nhãn email tự động. Xem skill `gmail-label`       | Gmail OAuth qua MCP server        |

### Cập Nhật Dự Án (Perplexity)

Khi user nói **"Cập nhật dự án [Tên]"** hoặc **"Cập nhật thông tin [Tên dự án]"**, Claude phải:

1. Map tên sang slug: Sun Symphony R5 → `sun-symphony-residence5`, Vinhomes Hải Vân Bay → `vinhomes-hai-van-bay`, FourS Tower → `fours-tower`
2. Chạy research với query toàn diện:

```bash
python3 scripts/research_bot.py \
  "[Tên dự án] Đà Nẵng tổng quan vị trí pháp lý tiến độ giai đoạn mở bán booking giá chính thức giá hiện tại giá thứ cấp sang nhượng giá rumor chính sách bán hàng thanh toán 2026" \
  --output context/projects/<slug>.md \
  --recency month
```

3. Đọc kết quả, so sánh với file cũ, tóm tắt cho user những điểm **thay đổi hoặc mới** so với lần cập nhật trước.

**Thông tin bắt buộc phải có khi cập nhật dự án:**

- Tổng quan & vị trí dự án
- Giai đoạn hiện tại (phân khu nào đang mở / sắp mở)
- Tình trạng pháp lý (loại sổ, giấy phép)
- Tiến độ xây dựng & ngày bàn giao
- Ngày mở bán / nhận booking
- Giá chính thức hiện tại (có bảng nếu có)
- Giá thứ cấp / sang nhượng nếu dự án đã mở bán (tìm trên các sàn batdongsan, homedy, nha.vn)
- Giá rumor đang lan truyền trong cộng đồng môi giới (ghi rõ nguồn)
- Xu hướng giá so với đợt mở bán trước
- Chính sách bán hàng (thanh toán, lãi suất, chiết khấu)

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
