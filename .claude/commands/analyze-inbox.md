# Analyze Inbox

Phân tích tất cả links/content trong `context/intelligence/inbox.md` phần `## PENDING`.

---

## Quy Trình

1. Đọc `context/intelligence/inbox.md` — tìm section `## PENDING`
2. Nếu PENDING trống: báo "Inbox trống, không có gì cần xử lý."
3. Với mỗi item trong PENDING:
   - Detect loại source từ URL hoặc nội dung
   - Chạy tool phù hợp (xem bảng bên dưới)
   - Phân tích, tạo entry chuẩn
4. Edit file: xóa item khỏi PENDING, append entry vào section chủ đề đúng
5. Báo cáo ngắn: "Đã xử lý X items" + tóm tắt 1 dòng mỗi cái

---

## Tool Routing

| Loại source | Detect bằng                                                                               | Tool       | Lệnh                                                                                                                                                            |
| ----------- | ----------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| YouTube     | youtube.com / youtu.be trong URL                                                          | Gemini     | `node -e "import('./analyze-video.js').then(m => m.analyzeVideo('URL', 'Tóm tắt nội dung chính, extract 3 hook ideas phù hợp BĐS Đà Nẵng')).then(console.log)"` |
| Bài báo     | URL chứa domain báo (vnexpress, cafef, tuoitre, thanhnien, dantri, batdongsan, homedy...) | Perplexity | `python3 scripts/research_bot.py "URL" --output /tmp/inbox_result.md --recency month` rồi `cat /tmp/inbox_result.md`                                            |
| TikTok      | tiktok.com trong URL                                                                      | Apify      | Actor `clockworks/free-tiktok-scraper`, input `{"postURLs": ["URL"]}`, extract caption + stats                                                                  |
| Facebook    | facebook.com trong URL                                                                    | Note       | Thường bị login wall — ghi chú "Facebook: cần xử lý thủ công" vào entry, không bỏ qua                                                                           |
| Raw text    | Không có URL                                                                              | Claude     | Phân tích trực tiếp từ nội dung paste                                                                                                                           |

---

## Format Entry Chuẩn (sau phân tích)

```
### Tiêu đề ngắn gọn mô tả nội dung
**Nguồn:** URL | **Tên nguồn:** Tên hiển thị (vd: VnExpress, Cổng TTĐT Đà Nẵng, Cafef) | **Thêm:** YYYY-MM-DD | **Status:** PENDING
**Tags:** #thị-trường | #dự-án | #nghề | #cá-nhân — kèm format phù hợp: #carousel #video #ảnh

**Tóm tắt:** 3-5 dòng core message bằng tiếng Việt

**Data/Quotes:**
- Con số hoặc quote cụ thể đáng dùng trong bài (ghi rõ: nguồn: Tên nguồn)

**Hook ideas:**
1. Hook phù hợp carousel hoặc ảnh cá nhân
2. Hook phù hợp video market
3. Hook thay thế (góc độ khác)
```

**Quy tắc viết entry:**

- Tóm tắt và hook ideas bằng tiếng Việt hoàn toàn
- Hook ideas viết sẵn theo giọng Bình — thô, đời, không corporate
- Không dùng dấu gạch `—` hay `-` trong hook ideas (quy tắc chung)
- Tags dùng format nhóm chủ đề + format phù hợp
- **Tên nguồn** phải là tên hiển thị dễ đọc, không phải raw domain:
  - `danang.gov.vn` → "Cổng TTĐT Đà Nẵng"
  - `vnexpress.net` → "VnExpress"
  - `cafef.vn` → "CafeF"
  - `tuoitre.vn` → "Tuổi Trẻ"
  - `batdongsan.com.vn` → "BatDongSan.com.vn"
  - `homedy.com` → "Homedy"
  - `dantri.com.vn` → "Dân Trí"
  - Domain khác → dùng domain gốc (vd: `www.xxx.vn`)

**Quy tắc cite và dùng data inbox khi viết bài:**

**Nguyên tắc chung:**

- 1 entry không phải 1 bài. 1 nguồn có thể cung cấp data cho nhiều bài khác nhau.
- Nhiều entries có thể kết hợp thành 1 bài — khuyến khích dùng chéo nhiều nguồn để luận điểm đa chiều.
- Thông tin chung (số liệu thị trường, chính sách, hạ tầng) là kiến thức nền — dùng thoải mái khi relevant, không cần map 1-1 với entry.

**Khi dùng data/số liệu cụ thể từ nguồn — cite trong bài:**

- Format: `(nguồn: Tên nguồn)` hoặc `theo Tên nguồn`
- Ví dụ: "Tỷ suất cho thuê ven biển đạt 9-10%/năm (nguồn: CafeF)"
- Ví dụ: "Theo Cổng TTĐT Đà Nẵng, dự án metro tuyến số 2 dự kiến khởi công 2027"
- Không cần full URL, chỉ tên nguồn là đủ

**Khi tổng hợp đa nguồn hoặc diễn giải theo góc nhìn Bình — thêm ghi chú duyệt:**

Nếu bài viết dùng phân tích tổng hợp từ nhiều nguồn, hoặc Claude đưa ra luận điểm/nhận định dựa trên kiến thức chung (không phải trích dẫn trực tiếp), **BẮT BUỘC** thêm ghi chú vào `post.md` phần cuối để Bình biết duyệt kỹ hơn:

```
> Ghi chú duyệt: Bài này dùng phân tích tổng hợp từ [nguồn A + nguồn B] / diễn giải theo góc nhìn Bình.
> Số liệu: [liệt kê số liệu cụ thể và nguồn gốc].
> Bình kiểm tra lại trước khi đăng.
```

Không thêm ghi chú này nếu bài chỉ dùng trải nghiệm cá nhân Bình (storytelling, kinh nghiệm nghề) — không cần verify số liệu.

---

## Bộ Lọc Thương Hiệu — Dùng Khi Scan Inbox Trước Tạo Content

**Inbox là kho kiến thức, không phải queue content.** Bình paste nhiều link để có góc nhìn đa chiều, nhưng không phải entry nào cũng thành bài. Chỉ đề xuất entry khi khớp định hướng thương hiệu.

**Chủ đề có thể dùng làm content:**

| Nhóm                       | Ví dụ                                                                   |
| -------------------------- | ----------------------------------------------------------------------- |
| Thị trường căn hộ Đà Nẵng  | Giá, xu hướng, thanh khoản, tỷ suất cho thuê                            |
| Hạ tầng Đà Nẵng            | Metro, sân bay, bến du thuyền, khu kinh tế                              |
| Pháp lý BĐS                | Sổ đỏ/sổ hồng, thủ tục mua bán, quy định mới có ảnh hưởng đến người mua |
| Dự án focus                | Symphony 5, FourS Tower, thông tin các dự án cạnh tranh                 |
| Kinh nghiệm nghề môi giới  | Chuyển đổi đất nền sang căn hộ, tư vấn, va chạm với khách               |
| Tư duy đầu tư BĐS          | Cách chọn sản phẩm, chu kỳ thị trường, rủi ro                           |
| AI và công cụ cho môi giới | Workflow, tiết kiệm thời gian, community video                          |

**Chủ đề lưu để tham khảo, KHÔNG dùng làm content trực tiếp:**

- Tin tức chính trị, kinh tế vĩ mô không gắn với BĐS Đà Nẵng
- Nhà ở xã hội (không phải phân khúc Bình bán) → chỉ dùng làm background data khi phân tích cung/cầu
- Thủ tục hành chính thuần túy → chỉ dùng làm data điểm trong bài có góc nhìn từ Bình
- Bất kỳ chủ đề nào không có góc nhìn cá nhân Bình hoặc không phục vụ tệp khách hàng mục tiêu

**Khi scan inbox trước tạo content:**

1. Đọc tất cả entries chưa [USED]
2. Lọc những entry khớp chủ đề batch đang tạo VÀ phù hợp định hướng thương hiệu
3. Chỉ đề xuất 2-3 entries relevant nhất — không list hết
4. Nếu entry là kiến thức nền (không dùng làm hook/bài trực tiếp được): dùng làm data/context trong bài nhưng không buộc phải tạo bài riêng

---

## Xác Định Section Đặt Entry

| Tags                              | Section trong file       |
| --------------------------------- | ------------------------ |
| #thị-trường                       | `## Thị Trường`          |
| #dự-án                            | `## Dự Án`               |
| #nghề                             | `## Nghề`                |
| #cá-nhân hoặc #cộng-đồng hoặc #ai | `## Cá Nhân / Cộng Đồng` |
| Nhiều tags                        | Section của tag đầu tiên |

---

## Giới Hạn File

Nếu tổng entries (bao gồm [USED]) vượt 50: xóa entries cũ nhất có `Status: [USED: ...]` trước.
Entries `Status: PENDING` (chưa dùng) không xóa trừ khi user yêu cầu.
