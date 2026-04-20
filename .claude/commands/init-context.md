# Init — Tạo Context Từ URL

Khởi tạo toàn bộ context của workspace cho một người dùng mới. Command này nhận URL và/hoặc text, scrape mọi nguồn có thể, phân tích dữ liệu và xây toàn bộ file context, đồng thời cập nhật `CLAUDE.md`.

**Command này có tính phá hủy** — nó sẽ ghi đè các file context hiện có. Chỉ dùng khi setup ban đầu hoặc khi muốn reset toàn phần.

## Đầu Vào

User truyền vào `$ARGUMENTS`, có thể là bất kỳ tổ hợp nào của:

- URL LinkedIn profile (ví dụ `https://www.linkedin.com/in/username/`)
- URL YouTube channel (ví dụ `https://www.youtube.com/@ChannelName`)
- URL Instagram (ví dụ `https://www.instagram.com/username/`)
- URL Twitter/X (ví dụ `https://x.com/username`)
- URL website (ví dụ `https://example.com`)
- Text tự do (bio, mô tả business, mục tiêu, ghi chú, bất cứ thông tin gì)

Yêu cầu tối thiểu: ít nhất MỘT social profile URL hoặc đủ text để hiểu người đó là ai.

## Các Bước Thực Hiện

### Giai Đoạn 1: Phân Tích Đầu Vào

1. Phân tích `$ARGUMENTS` để xác định:
   - LinkedIn URL (nếu có)
   - YouTube URL (nếu có)
   - Instagram URL (nếu có)
   - Twitter/X URL (nếu có)
   - Website URL (nếu có)
   - Phần text tự do (mọi thứ không phải URL)

2. Xác nhận những gì đã nhận diện được rồi tiến hành luôn, không cần chờ user duyệt.

### Giai Đoạn 2: Scrape Mọi Nguồn (song song)

Chạy đồng thời tất cả scraper phù hợp. Đọc API key trực tiếp từ file `.env` (không dùng `source .env` vì dễ fail im lặng).

**LinkedIn Profile + Posts** (nếu có LinkedIn URL):

```python
# Profile scraper — actor: 2SyF0bMFpUje24Gqt (LinkedIn Profile Scraper)
import requests
APIFY_KEY = "<đọc từ .env>"
resp = requests.post(
    "https://api.apify.com/v2/acts/2SyF0bMFpUje24Gqt/runs",
    headers={"Authorization": f"Bearer {APIFY_KEY}", "Content-Type": "application/json"},
    json={"profileUrls": ["<LINKEDIN_URL>"]}
)
run_id = resp.json()["data"]["id"]
# Poll: GET https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_KEY}
# Results: GET https://api.apify.com/v2/actor-runs/{run_id}/dataset/items?token={APIFY_KEY}
```

```python
# Posts scraper — actor: apimaestro~linkedin-profile-post-scraper (LinkedIn Profile Posts)
resp = requests.post(
    "https://api.apify.com/v2/acts/apimaestro~linkedin-profile-post-scraper/runs",
    headers={"Authorization": f"Bearer {APIFY_KEY}", "Content-Type": "application/json"},
    json={"profileUrls": ["<LINKEDIN_URL>"], "maxPosts": 100}
)
```

**YouTube Channel + Videos** (nếu có YouTube URL):

```python
# YouTube scraper — actor: streamers~youtube-scraper
resp = requests.post(
    "https://api.apify.com/v2/acts/streamers~youtube-scraper/runs",
    headers={"Authorization": f"Bearer {APIFY_KEY}", "Content-Type": "application/json"},
    json={"startUrls": [{"url": "<YOUTUBE_URL>/videos"}], "maxResults": 50}
)
```

**Website** (nếu có website URL):

- Dùng WebFetch để lấy trang chủ và các trang quan trọng như about, services, pricing
- Trích xuất: tên công ty, value proposition, khách hàng mục tiêu, dịch vụ

**Instagram** (nếu có Instagram URL):

```python
# Instagram scraper — actor: apify~instagram-profile-scraper
resp = requests.post(
    "https://api.apify.com/v2/acts/apify~instagram-profile-scraper/runs",
    headers={"Authorization": f"Bearer {APIFY_KEY}", "Content-Type": "application/json"},
    json={"usernames": ["<USERNAME>"]}
)
```

**Twitter/X** (nếu có Twitter URL):

- Dùng WebSearch để tìm thông tin công khai về account
- Trích xuất: bio, follower count, content themes

### Giai Đoạn 3: Chờ Scraper Hoàn Thành

Poll tất cả tác vụ Apify đang chạy mỗi 10 giây cho tới khi hoàn tất (timeout: 3 phút mỗi task).

```python
import time
while True:
    time.sleep(10)
    r = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_KEY}")
    status = r.json()["data"]["status"]
    if status == "SUCCEEDED":
        results = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items?token={APIFY_KEY}").json()
        break
    elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
        break
```

### Giai Đoạn 4: Lưu Dữ Liệu Gốc

Lưu toàn bộ dữ liệu scrape vào `context/data/`:

```
context/data/
├── linkedin/
│   ├── profile.json
│   └── posts.json
├── youtube/
│   └── videos.json
├── instagram/
│   └── profile.json
└── twitter/
    └── profile.json
```

Chỉ tạo thư mục/file cho những nền tảng thực sự đã scrape.

### Giai Đoạn 5: Phân Tích Và Tạo File Context

Dùng toàn bộ dữ liệu thu thập được (scrape + text tự do) để tạo 4 file context:

**`context/profile.md`** — NGƯỜI ĐÓ LÀ AI:

- Họ tên, khu vực, chức danh chuyên môn
- Toàn bộ social profile URL cùng headline/bio hiện tại
- Bảng content platforms (đang dùng nền tảng nào, cho ai, nội dung gì)
- Phân tích voice & personality từ các bài đã scrape
- Ghi chú về ảnh cá nhân trong `context/images/` (user sẽ tự thêm sau)

**`context/business.md`** — HỌ ĐANG LÀM GÌ:

- Tên công ty/business và mô tả
- Sản phẩm/dịch vụ là gì
- Tệp khách hàng mục tiêu / ICP
- Mô hình doanh thu (nếu nhận ra được từ nội dung)
- Products & services
- Thông tin nổi bật, khách hàng, kết quả

**`context/strategy.md`** — HỌ ĐANG ĐI ĐÂU:

- Trọng tâm hiện tại và sứ mệnh (suy ra từ content gần đây)
- Các ưu tiên (xếp theo tần suất nội dung và engagement)
- Success metrics
- Các câu hỏi mở / tension chiến lược

**`context/metrics.md`** — CÁC CON SỐ HIỆN TẠI:

- Follower/subscriber theo từng nền tảng
- Nội dung hiệu quả nhất (theo view/engagement)
- Bảng kiểm kê dữ liệu đã scrape
- Ngày cập nhật gần nhất

### Giai Đoạn 6: Phân Tích Giọng Viết

Từ các bài đã scrape, phân tích pattern viết:

- Hook thường dùng
- Cấu trúc câu (ngắn/dài, mảnh câu, câu hỏi)
- Tone pattern (formal/casual, vulnerable/authoritative)
- Cụm từ lặp lại hoặc verbal tics
- Cách dùng số liệu, câu chuyện, danh sách
- CTA pattern

Lưu vào `context/voice-analysis.md` để làm tài liệu tham chiếu cho AI bắt chước giọng.

### Giai Đoạn 7: Xác Định ICP

Từ business context, content themes và engagement patterns, xây:

**`context/icp.md`** — HỌ PHỤC VỤ AI:

- ICP chính (vai trò, ngành, quy mô công ty, pain points)
- ICP phụ nếu có
- Những chủ đề nội dung mà tệp này tương tác nhiều nhất
- Những vấn đề họ đang cố giải quyết
- Họ dành thời gian ở đâu (nền tảng nào)
- Họ dùng ngôn ngữ/jargon gì
- Điều gì khiến họ mua / hành động

### Giai Đoạn 8: Cập Nhật CLAUDE.md

Cập nhật phần "Who You Are" và các phần cá nhân hóa trong `CLAUDE.md`:

- Thay placeholder bằng thông tin thật
- Cập nhật social profile links
- Cập nhật bảng content platforms
- Cập nhật voice & tone guidelines theo voice analysis
- Giữ nguyên tài liệu command, cấu trúc workspace và workflow docs

### Giai Đoạn 9: Báo Cáo Tóm Tắt

In ra báo cáo dạng:

```text
Đã khởi tạo context cho [Full Name]

Nguồn đã scrape:
  - LinkedIn: [X] posts, [Y] connections, [Z] followers
  - YouTube: [X] videos, [Y] subscribers
  - Website: [pages fetched]

Các file đã tạo:
  - context/profile.md
  - context/business.md
  - context/strategy.md
  - context/metrics.md
  - context/voice-analysis.md
  - context/icp.md
  - context/data/[platform]/...

CLAUDE.md đã được cập nhật theo danh tính mới.

Bước tiếp theo:
  1. Thêm ảnh cá nhân vào context/images/
  2. Thêm 3 ảnh tham chiếu infographic vào reference/ (infographic-ref-1.jpeg, infographic-ref-2.jpeg, infographic-ref-3.jpeg)
  3. Chạy /prime để kiểm tra context
  4. Bắt đầu tạo nội dung với /create-10-posts
```

---

## Lưu Ý Quan Trọng

- **Scrape song song:** Submit tất cả job Apify cùng lúc rồi poll tất cả. Không chờ từng cái chạy xong mới bắt đầu cái tiếp theo.
- **Giảm cấp mềm mại:** Nếu một scraper fail hoặc không có URL tương ứng, bỏ qua nguồn đó và dùng những gì đang có.
- **Không bịa:** Chỉ viết context dựa trên dữ liệu thật. Nếu không xác định được, ghi là "TBD" hoặc "Chưa xác định — cần thêm thủ công."
- **Chất lượng phân tích giọng viết:** Càng nhiều post càng tốt. Nếu có dưới 10 post, phải ghi rõ phân tích này còn sơ bộ.
- **ICP chỉ là giả thuyết ban đầu:** ICP được suy ra từ content themes và engagement. User nên review lại.
- **API keys:** Đọc `APIFY_API_KEY` trực tiếp từ `.env` bằng Python. Không dựa vào shell `source`.
