# update-intelligence

Cập nhật intelligence files từ Apify TikTok.
Ngân sách: ~$2.00/lần — 2 lần/tháng trong $5 free tier Apify.

## Bước 1 — Chạy scraper

```bash
python3 scripts/update-intelligence.py
```

Chờ 3–5 phút. Script tự động:

- Scrape 300 posts từ 12 hashtag BĐS Đà Nẵng (~$1.50)
- Lọc bài views ≥ 10,000 + có keyword BĐS trong caption
- Chọn top 5 bài nhiều comment nhất
- Scrape top 20 comments (sort by likes) từ mỗi bài (~$0.50)
- In SUMMARY để Claude đọc

## Bước 2 — Phân tích posts → viral-patterns.md

Từ TIKTOK POSTS SUMMARY:

- Nhóm theo hook-type: **Confession** / **Data Lead** / **Paradox** / **Story Open**
- Mỗi pattern: hook mẫu, cấu trúc thân bài, format visual, tại sao hoạt động, gợi ý angle cho Bình Phan
- Giữ top 12–15 patterns, bỏ bài trùng nhau

## Bước 3 — OVERWRITE viral-patterns.md

- Thay toàn bộ nội dung, không giữ lại dữ liệu cũ
- Cập nhật `Cập nhật lần cuối: DD/MM/YYYY`
- Giữ cấu trúc 4 nhóm hook-type

## Bước 4 — Phân tích comments → audience-painpoints.md

Từ TIKTOK COMMENTS SUMMARY:

- Phân vào 6 nhóm cố định: pháp lý / tài chính / thời điểm mua / rủi ro dự án / so sánh / cho thuê
- Comment nhiều likes = pain point của số đông, ưu tiên phân tích
- Paraphrase — không copy nguyên văn

## Bước 5 — OVERWRITE nội dung audience-painpoints.md

- Giữ nguyên 6 nhóm chủ đề, thay toàn bộ nội dung bên trong
- Cập nhật timestamp

## Bước 6 — Báo cáo

Tóm tắt: số patterns, số comments, chi phí ước tính, ngày nhắc tiếp theo.
