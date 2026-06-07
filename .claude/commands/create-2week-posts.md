# Tạo Stock 2 Tuần — Carousel + Ảnh Cá Nhân

Tạo đúng **16 bài** cho 2 tuần lịch đăng: 4 Carousel + 12 Ảnh cá nhân.

Không tạo infographic, video, hay Market post.

---

## Số Lượng Chuẩn

| Loại        | Style              | Số bài | Kênh đăng              | Slot    |
| ----------- | ------------------ | ------ | ---------------------- | ------- |
| Carousel    | T2 — góc nhìn Bình | 2      | BMN                    | T2 8am  |
| Carousel    | T6 — khách quan    | 2      | BMN                    | T6 8am  |
| Ảnh cá nhân | —                  | 2      | Kênh CN                | T3 12pm |
| Ảnh cá nhân | —                  | 2      | BMN                    | T4 8am  |
| Ảnh cá nhân | —                  | 2      | Kênh CN + IG + Threads | T5 12pm |
| Ảnh cá nhân | —                  | 2      | BMN                    | T6 12pm |
| Ảnh cá nhân | —                  | 2      | Kênh CN                | T7 12pm |
| Ảnh cá nhân | —                  | 2      | Kênh CN + IG + Threads | CN 12pm |
| **Tổng**    |                    | **16** |                        |         |

---

## BƯỚC 1 — NẠP CONTEXT

Đọc các file sau (không hỏi, tự đọc):

- `context/voice-analysis.md`
- `context/strategy.md`
- `context/career-history.md` — kho chuyện thật để chọn góc độ
- `context/intelligence/audience-painpoints.md`
- `context/intelligence/viral-patterns.md`
- `outputs/post-registry.md` — đọc **15 bài cuối cùng** để tránh trùng hook-type và chủ đề

---

## BƯỚC 2 — LẬP KẾ HOẠCH 16 BÀI (CHỜ DUYỆT TRƯỚC KHI VIẾT)

Trình bày bảng kế hoạch. Chờ user xác nhận rồi mới viết nội dung.

**Carousel (4 bài):**

| #   | Tuần | Ngày | Chủ đề                     | Hook dự kiến |
| --- | ---- | ---- | -------------------------- | ------------ |
| C1  | 1    | T2   | Thị trường — góc nhìn Bình | ...          |
| C2  | 1    | T6   | Thị trường — khách quan    | ...          |
| C3  | 2    | T2   | Thị trường — góc nhìn Bình | ...          |
| C4  | 2    | T6   | Thị trường — khách quan    | ...          |

**Ảnh cá nhân (12 bài):**

| #   | Tuần | Ngày | Kênh  | Pillar | Hook dự kiến |
| --- | ---- | ---- | ----- | ------ | ------------ |
| A1  | 1    | T3   | CN    | ...    | ...          |
| A2  | 1    | T4   | BMN   | ...    | ...          |
| A3  | 1    | T5   | CN+IG | ...    | ...          |
| A4  | 1    | T6   | BMN   | ...    | ...          |
| A5  | 1    | T7   | CN    | ...    | ...          |
| A6  | 1    | CN   | CN+IG | ...    | ...          |
| A7  | 2    | T3   | CN    | ...    | ...          |
| A8  | 2    | T4   | BMN   | ...    | ...          |
| A9  | 2    | T5   | CN+IG | ...    | ...          |
| A10 | 2    | T6   | BMN   | ...    | ...          |
| A11 | 2    | T7   | CN    | ...    | ...          |
| A12 | 2    | CN   | CN+IG | ...    | ...          |

**Quy tắc đa dạng bắt buộc khi lập kế hoạch:**

- 12 Ảnh cá nhân phải trải đều 5 pillars — không pillar nào vượt 3 bài:
  1. Kinh nghiệm cũ làm nền
  2. Tự nhận diện (mạnh/yếu, đang làm gì với nó)
  3. Va chạm & bài học (tình huống mới với khách căn hộ)
  4. Tư duy chuyển đổi (thinking outside the box)
  5. Mindset vận động (rủi ro lớn nhất là đứng yên)
- Không dùng cùng hook-type quá 3 lần trong 12 Ảnh
- Không 2 bài liền nhau cùng hook-type
- T5 và CN đăng lên IG + Threads — tránh đề cập dự án cụ thể (Symphony, FourS...)
- Carousel T2 vs T6 phải rõ tông khác nhau: "mình thấy..." vs "dữ liệu cho thấy..."

---

## BƯỚC 3 — VIẾT NỘI DUNG

Viết từng bài theo thứ tự. Với mỗi bài tạo thư mục `posts/NNN-slug/`.

### Carousel (4 bài)

Với mỗi Carousel:

1. Viết `content.json` theo format chuẩn (xem CLAUDE.md)
2. Viết `post.md` với caption đầy đủ (plain text)
3. Ghi rõ ảnh cover dùng:
   - T2: ảnh chân dung Bình (`IMG_7928.jpg` hoặc phù hợp)
   - T6: ảnh đẹp không có Bình — ghi `[CẦN ẢNH CHẤT LƯỢNG CAO — CHƯA CÓ]`
4. **Không chạy** `generate-carousel.py` — chờ user review `content.json` xong

Template metadata trong post.md:

```
**Lịch đăng:** Tuần X — Thứ X — 8:00am — BMN
**Style:** T2 — Góc nhìn Bình / T6 — Khách quan
```

### Ảnh Cá Nhân (12 bài)

Với mỗi Ảnh:

1. Viết `post.md` với text đầy đủ (plain text, copy-paste được)
2. Gợi ý ảnh từ `context/images/` phù hợp vibe
3. Viết lệnh `add-photo-overlay.py` vào Image Notes — **chưa chạy**
4. Với bài đăng IG + Threads (T5, CN): kiểm tra không mention dự án cụ thể

Template metadata trong post.md:

```
**Lịch đăng:** Tuần X — Thứ X — 12:00pm — [Kênh]
**Pillar:** [tên pillar]
```

---

## BƯỚC 4 — CẬP NHẬT REGISTRY VÀ DASHBOARD

Sau khi viết xong tất cả 16 bài:

1. Append 16 dòng vào `outputs/post-registry.md` (format chuẩn)
2. Chạy `python3 scripts/build-dashboard.py`

---

## Không Làm Trong Command Này

- Không generate ảnh qua Kie.ai
- Không chạy `add-photo-overlay.py`
- Không chạy `generate-carousel.py`
- Không tạo infographic
- Không tạo bài Market video hay Community video
