# Tạo Batch 10 Nội Dung

Tạo 10 nội dung sẵn sàng xuất bản trong một lần chạy.

Mỗi nội dung phải tự đứng được một mình, không phụ thuộc vào follow-up như "comment X để lấy tài liệu" hay "nhắn tin mình để nhận file".

## Cơ Cấu Nội Dung

### Theo Phương Pháp (ý tưởng đến từ đâu)

| Phương pháp       | Số lượng | Mô tả                                                                          |
| ----------------- | -------- | ------------------------------------------------------------------------------ |
| Viral Replication | 5        | Tìm nội dung đã chứng minh hiệu quả, lấy cấu trúc đóng gói, đổi phần substance |
| Trend Surfing     | 3        | Bám các xu hướng đang nổi lên ngay bây giờ trong niche                         |
| Pain Points       | 2        | Đào sâu nỗi đau thật của khán giả và đưa giải pháp hành động được              |

### Theo Định Dạng (nội dung được đưa ra như thế nào)

Mỗi nội dung **bắt buộc phải có visual**. Không có bài text-only.

| Định dạng             | Số lượng | Mô tả                                                            |
| --------------------- | -------- | ---------------------------------------------------------------- |
| Text + Ảnh cá nhân    | 4        | Nội dung chữ + ảnh lấy từ `context/images/` phù hợp với vibe bài |
| Text + AI Infographic | 4        | Nội dung chữ + infographic tạo bằng Kie.ai có `reference_image`  |
| Carousel (PDF)        | 2        | Carousel 7-11 slide tạo bởi `scripts/generate-carousel.py`       |

### Ma Trận Phân Bổ

Phân phối phương pháp qua các định dạng để đảm bảo đa dạng. Không để hai bài trùng cả **phương pháp** lẫn **định dạng**. Ví dụ:

| #   | Phương pháp       | Định dạng             | Ghi chú            |
| --- | ----------------- | --------------------- | ------------------ |
| 1   | Viral Replication | Text + Ảnh cá nhân    |                    |
| 2   | Viral Replication | Text + AI Infographic |                    |
| 3   | Viral Replication | Carousel              |                    |
| 4   | Viral Replication | Text + AI Infographic | Khác chủ đề bài #2 |
| 5   | Viral Replication | Text + Ảnh cá nhân    | Khác chủ đề bài #1 |
| 6   | Trend Surfing     | Text + AI Infographic |                    |
| 7   | Trend Surfing     | Text + Ảnh cá nhân    |                    |
| 8   | Trend Surfing     | Carousel              |                    |
| 9   | Pain Point        | Text + AI Infographic |                    |
| 10  | Pain Point        | Text + Ảnh cá nhân    |                    |

**Thứ tự định dạng phải được xáo trộn** để hai bài liên tiếp không trùng format.

---

## QUY TẮC QUAN TRỌNG

### Đa Dạng (không được thỏa hiệp)

10 nội dung phải đa dạng trên mọi chiều:

1. **Đa dạng chủ đề** — Không có 2 bài nói cùng một chủ đề hẹp. Phải phủ ít nhất 5 chủ đề con khác nhau.
2. **Đa dạng hook** — Luân phiên các kiểu hook:
   - Dạng số liệu: "7 công cụ...", "mình đã dành 200 giờ..."
   - Dạng trái chiều: "Đừng làm X nữa. Đây là lý do."
   - Dạng kể chuyện: "6 tháng trước mình..."
   - Dạng câu hỏi: "Tại sao 90% founder thất bại ở...?"
   - Dạng thú nhận: "Mình đã sai về..."
   - Dạng tuyên bố mạnh: "Chỉ một thay đổi này giúp..."
   - Không để 2 bài liên tiếp cùng kiểu hook
3. **Đa dạng visual** — Feed phải thú vị khi lướt:
   - Ảnh cá nhân phải dùng các bối cảnh khác nhau
   - Infographic phải xoay reference khác nhau (`ref-1`, `ref-2`, `ref-3`)
   - Carousel nên khác số slide và kiểu minh họa
   - Không để 3 bài liền cùng một định dạng
4. **Đa dạng cảm xúc/tông**:
   - Có bài thiên về dạy kiến thức
   - Có bài dễ tổn thương/chia sẻ thất bại
   - Có bài bold/provocative
   - Có bài thực hành từng bước

### Tự Đứng Được Một Mình

Mỗi nội dung phải hoàn chỉnh và có thể xuất bản ngay:

- KHÔNG dùng CTA kiểu "Comment X mình gửi..."
- KHÔNG dùng "Link ở comment"
- KHÔNG dùng "DM mình để nhận..."
- CTA chấp nhận được: "Follow để xem thêm", "Lưu lại", "Chia sẻ cho team", "Quan điểm của bạn là gì?"
- Giá trị phải nằm ngay trong nội dung, không bị khóa sau một hành động

### Tiêu Chuẩn Chất Lượng

- Viết theo tinh thần Adam Robinson nhưng phải Việt hóa theo context hiện tại
- Mọi bài đều cần hook mạnh, vì 2 dòng đầu quyết định phần lớn hiệu quả
- Mỗi bài phải có giá trị thật, không viết cho có
- Dùng context thật: tên thương hiệu, số liệu thật, trải nghiệm thật
- Ưu tiên số cụ thể hơn phát biểu mơ hồ

---

## Các Bước Thực Hiện

### Giai Đoạn 1: Lên Ý Tưởng

1. Đọc lại các file context:
   - `context/profile.md`
   - `context/business.md`
   - `context/strategy.md`
   - `context/metrics.md`
   - `reference/adam-robinson-writing-style.md`
2. Kiểm tra 5 post gần nhất trong `posts/` để tránh lặp chủ đề
3. Tạo 5 ý tưởng Viral Replication
4. Tạo 3 ý tưởng Trend Surfing
5. Tạo 2 ý tưởng Pain Point
6. Gán format cho cả 10 ý tưởng
7. Lưu plan ý tưởng vào `outputs/YYYY-MM-DD-batch-content-plan.md`
8. Chuyển ngay sang bước tạo nội dung TEXT, không chờ user duyệt plan

### Giai Đoạn 2: Tạo Nội Dung Text (CHƯA tạo ảnh)

Với từng nội dung:

1. Xác định số post tiếp theo bằng cách kiểm tra thư mục `posts/`
2. Tạo thư mục mới theo chuẩn `posts/NNN-slug/`

**Nếu là Text + Ảnh cá nhân:**

1. Viết toàn bộ nội dung
2. Copy ảnh đã chọn từ `context/images/` thành `image.png`
3. Lưu `post.md`
4. Nếu là viral replication thì lưu thêm `original.md`

**Nếu là Text + AI Infographic:**

1. Viết toàn bộ nội dung
2. Lưu `post.md` và `original.md` nếu có
3. **CHƯA TẠO ẢNH** — chờ user duyệt nội dung ở Giai Đoạn 2.5

**Nếu là Carousel:**

1. Viết nội dung từng slide
2. Tạo file JSON bằng UTF-8 và giữ nguyên tiếng Việt có dấu
3. Viết caption/post đi kèm
4. Lưu `post.md` và `content.json`
5. **CHƯA TẠO PDF** — chờ user duyệt nội dung ở Giai Đoạn 2.5

### Giai Đoạn 2.5: Duyệt Nội Dung Trước Khi Tạo Visual (BẮT BUỘC)

**Bước này KHÔNG được bỏ qua.**

Trước khi generate bất kỳ ảnh nào (Kie.ai infographic hoặc carousel PDF), PHẢI:

1. Trình bày cho user danh sách tất cả nội dung đã viết, gồm:
   - Tiêu đề, phương pháp, định dạng
   - Nội dung text đầy đủ (hoặc tóm tắt hook + ý chính)
   - Với infographic: mô tả nội dung sẽ hiển thị trên ảnh
   - Với carousel: tóm tắt nội dung từng slide
2. Chờ user duyệt và chỉnh sửa nếu cần
3. Chỉ sau khi user xác nhận, mới chuyển sang Giai Đoạn 3

**Lý do:** Tạo ảnh tốn API call và thời gian. Nếu nội dung không dùng được thì lãng phí.

### Giai Đoạn 3: Tạo Visual (sau khi user duyệt)

**Nếu là Text + AI Infographic:**

1. Tạo infographic bằng Kie.ai với `reference_image`
2. Mọi text hiển thị trong ảnh phải giữ nguyên tiếng Việt có dấu — prompt PHẢI chứa đúng tiếng Việt có dấu, KHÔNG gửi prompt không dấu
3. Luân phiên `reference/infographic-ref-1.jpeg`, `ref-2`, `ref-3`
4. Lưu `image.png`
5. Kiểm tra text trên ảnh — nếu sai dấu tiếng Việt, regenerate hoặc dùng Pillow để sửa

**Nếu là Carousel:**

1. Chạy `python scripts/generate-carousel.py --json <file> --output posts/NNN-slug/carousel.pdf`

### Giai Đoạn 3: Hoàn Thiện

1. Chạy `python3 scripts/build-dashboard.py`
2. Kiểm tra mọi nội dung đều có visual:
   - `image.png`, hoặc
   - `carousel.pdf` + `carousel-slides/`
3. Kiểm tra chất lượng:
   - Không trùng chủ đề
   - Hook đa dạng
   - `post.md` có phần `## Post Text (copy-paste ready)`
   - Trường format khớp với visual thật
4. Báo cáo lại:
   - Liệt kê 10 nội dung đã tạo với số, tiêu đề, phương pháp, định dạng
   - Mở dashboard bằng `open outputs/dashboard.html`

---

## Chuẩn Lưu Trữ Post

Mỗi post nằm trong `posts/NNN-slug/`:

```text
post.md
image.png
carousel.pdf
original.md
original-image.jpg
```

### Mẫu `post.md`

```markdown
# [Tiêu đề bài]

**Date created:** YYYY-MM-DD
**Method:** [Viral Replication / Trend Surfing / Pain Point]
**Format:** [Text + Personal Photo / Text + AI Infographic / Carousel]
**Platform:** [Điền nền tảng phù hợp]
**Status:** Ready to publish

## Post Text (copy-paste ready)

[Nội dung chính]

## Image Notes

[Ghi chú về ảnh/carousel]

## Original Post (if applicable)

[Link bài gốc, tác giả, engagement]
```

---

## Ghi Chú Về Song Song Hóa

- Phần ideation cho 3 phương pháp có thể chạy song song
- Các lệnh tạo hình Kie.ai có thể submit song song rồi poll song song
- Carousel PDF được tạo local nên khá nhanh
- Copy ảnh gần như tức thời
- Viết text thường nên làm tuần tự để giữ chất lượng
