---
Nguồn: Điền thủ công — dùng research_bot.py (Perplexity) khi cần số liệu cụ thể
Cập nhật: Khi có nhu cầu tạo bài thị trường/giá — không scrape tự động
Cách dùng: Ghi chú nhanh số liệu đã verify — để Claude tham khảo khi viết bài thị trường
---

# Market Pulse — Ghi Chú Số Liệu Thị Trường

> File này KHÔNG scrape tự động từ batdongsan.com.vn hay bất kỳ sàn rao vặt nào.
> Khi cần số liệu chính xác, chạy: `python3 scripts/research_bot.py "<query>" --recency month`
> Chỉ ghi vào đây những số liệu đã được verify và muốn tái sử dụng trong nhiều bài.

---

## Số Liệu Đã Verify

_(Trống — điền thủ công khi cần)_

Format ghi:

```
- [Số liệu]: [Nguồn] — [Ngày verify]
  Ví dụ: Tỷ suất cho thuê căn hộ Đà Nẵng Q1/2026: 5–6%/năm — Perplexity — 15/05/2026
```

---

## Ghi Chú Nhanh

_(Ghi tạm những thông tin chưa verify nhưng đang lưu hành trong ngành)_
