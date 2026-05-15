# /update-intelligence

Cập nhật intelligence files từ Apify (TikTok viral patterns + Facebook pain points).
Ngân sách: ~$1.65/lần — nằm trong $5 free tier Apify (2 lần/tháng).

## Quy trình

### Bước 1 — Chạy Apify scraper

```bash
python3 scripts/update-intelligence.py
```

Chờ script hoàn tất (2–5 phút). Script sẽ in SUMMARY để Claude đọc.

### Bước 2 — Phân tích TikTok summary

Từ danh sách top posts in ra:

- Nhóm theo hook-type: **Confession** / **Data Lead** / **Paradox** / **Story Open**
- Mỗi pattern ghi: hook mẫu, cấu trúc thân bài, format visual, tại sao hoạt động, gợi ý angle cho Bình Phan
- Giữ tối đa 12–15 patterns có views cao nhất, bỏ các bài trùng nhau

### Bước 3 — OVERWRITE `context/intelligence/viral-patterns.md`

- Thay toàn bộ nội dung (không giữ lại từ lần trước)
- Cập nhật frontmatter `Cập nhật lần cuối: DD/MM/YYYY`
- Giữ nguyên cấu trúc 4 nhóm hook-type

### Bước 4 — Phân tích Facebook comments (nếu có)

Nếu script trả về comment data:

- Phân loại vào 6 nhóm chủ đề cố định
- Paraphrase — không copy nguyên văn bất kỳ comment nào
- Ghi tần suất và mức độ lo lắng theo quan sát thực tế

### Bước 5 — OVERWRITE nội dung `context/intelligence/audience-painpoints.md`

- Giữ nguyên 6 nhóm chủ đề (không thêm, không xóa nhóm)
- Thay toàn bộ nội dung bên trong mỗi nhóm
- Cập nhật timestamp

### Bước 6 — Báo cáo

In ra:

- Số patterns TikTok tìm được
- Số comments phân tích được
- Chi phí Apify ước tính
- Ngày cập nhật tiếp theo (14 ngày sau)

## Lưu ý

- **Facebook comments** chỉ chạy nếu có URL trong `context/intelligence/fb-post-urls.txt`
  Thêm URL bài viral BĐS vào file đó (1 URL/dòng) trước khi chạy
- Raw data lưu tại `outputs/intelligence-raw/YYYY-MM-DD-*.json` để debug
- Không để 2 lần chạy trong cùng 1 ngày (tốn tiền, data không khác nhiều)
