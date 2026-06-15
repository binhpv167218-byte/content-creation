# Kế Hoạch: Hệ Thống Research Video YouTube

**Tạo lúc:** 2026-06-07  
**Mục tiêu:** Xây hệ thống phân tích video YouTube có thể lặp lại — input URL, output phân tích có cấu trúc, tích lũy thành kho pattern học được.

---

## Tại Sao Cần Hệ Thống?

Không phải xem rồi ghi chú rời rạc — mà mỗi video phân tích theo cùng 1 khung, lưu theo cùng 1 format. Sau 20–30 video sẽ thấy pattern nổi lên: hook nào lặp đi lặp lại, edit rhythm nào xuất hiện ở nhiều kênh khác nhau, cách dẫn chắt gọc nào phổ biến nhất.

---

## Phạm Vi Phân Tích — 5 Chiều

Mỗi video phân tích đúng 5 chiều, không thêm không bớt:

| #   | Chiều                    | Câu hỏi cốt lõi                                                                                           |
| --- | ------------------------ | --------------------------------------------------------------------------------------------------------- |
| 1   | **Hook & Opening**       | 3 giây đầu làm gì để giữ người xem? Loại hook: câu hỏi / số liệu / tình huống / visual shock / promise?   |
| 2   | **Cấu trúc nội dung**    | Bố cục tổng thể: mấy phần? Chuyển tiếp giữa các phần bằng cách nào? Có điểm "trả lời" cho hook đầu không? |
| 3   | **Visual Design & Edit** | Màu sắc chủ đạo, typography, nhịp cut, motion graphics, B-roll, ratio text/video                          |
| 4   | **Sound Design**         | BGM tone gì, SFX dùng khi nào, VO style (giọng thật / voice-over / chỉ text), sync âm thanh với hình      |
| 5   | **CTA & Ending**         | Kết bằng gì, CTA ở đâu (giữa / cuối), dạng CTA nào (follow / comment / link / nhắn tin)                   |

---

## Workflow Mỗi Lần Research

### Bước 1 — Chuẩn bị danh sách URL

Tạo 1 file text hoặc liệt kê trong chat. Mỗi URL kèm:

- Tên kênh
- Lý do chọn (viral / style đặc biệt / niche BĐS / editing đỉnh / ...)
- Số lượng: không giới hạn, nhưng 5–10 URL/batch cho dễ so sánh

### Bước 2 — Chạy phân tích từng video

Dùng `analyze-video.js` với prompt chuẩn bên dưới:

```bash
node -e "
import('./analyze-video.js').then(m => m.analyzeVideo(
  'YOUTUBE_URL',
  'Phân tích video này theo 5 chiều: (1) Hook 3 giây đầu — loại hook gì, làm thế nào để giữ người xem; (2) Cấu trúc nội dung — bao nhiêu phần, chuyển tiếp ra sao, có resolve hook không; (3) Visual design & edit rhythm — màu sắc, typography, nhịp cắt, motion graphics, text overlay; (4) Sound design — BGM tone, SFX khi nào, VO style, sync âm thanh; (5) CTA & ending — kết bằng gì, CTA ở đâu, dạng gì. Cuối cùng: 3 điểm đáng học nhất từ video này.'
)).then(console.log)"
```

### Bước 3 — Lưu kết quả vào `context/intelligence/video-templates.md`

Format chuẩn cho mỗi video (append vào cuối file):

```markdown
## Template N: [Tên ngắn mô tả style]

**Nguồn:** [Tên kênh] — [URL]  
**Ngày research:** YYYY-MM-DD  
**Lý do chọn:** [Viral / style đặc biệt / niche BĐS / ...]  
**Dài:** ~Xs  
**Dùng cho:** [Loại nội dung phù hợp áp dụng]

### Hook

[Mô tả hook 3 giây đầu — loại gì, cụ thể làm gì]

### Cấu trúc

[Sơ đồ thời gian: 0-Xs làm gì, Xs-Xs làm gì, ...]

### Visual Design

[Màu, font, nhịp cut, motion graphics đáng chú ý]

### Sound Design

[BGM tone, SFX pattern, VO style]

### CTA

[Vị trí, nội dung, dạng CTA]

### 3 Điểm Đáng Học

1. ...
2. ...
3. ...

---
```

### Bước 4 — Tổng hợp pattern sau mỗi 10 video (không bắt buộc ngay)

Khi đã có 10+ template, yêu cầu Claude đọc toàn bộ `video-templates.md` và rút ra:

- Hook-type nào xuất hiện nhiều nhất
- Edit rhythm phổ biến nhất (nhịp nhanh / trung bình / chậm)
- Sound pattern nào lặp lại
- CTA nào hiệu quả nhất

Lưu tổng hợp vào `context/intelligence/video-patterns-synthesis.md`.

---

## Danh Sách URL Đầu Tiên — Cần Bổ Sung

Bạn cần cung cấp danh sách URL muốn research. Gợi ý ưu tiên:

| Ưu tiên | Loại                                              | Lý do                            |
| ------- | ------------------------------------------------- | -------------------------------- |
| 1       | Video BĐS viral (TikTok / YouTube Shorts)         | Học hook và nội dung trong niche |
| 2       | Video phân tích thị trường có motion graphics đẹp | Học visual design                |
| 3       | Video talking head + data visualization           | Học cách kết hợp 2 format        |
| 4       | Video của đối thủ trong niche BĐS Đà Nẵng / VN    | Benchmark                        |
| 5       | Video ngoài niche có edit/style đặc biệt muốn học | Expand playbook                  |

---

## Thực Hiện

**Việc cần làm ngay:**

1. [ ] Bạn gửi danh sách URL muốn research (có thể gửi từng đợt)
2. [ ] Claude chạy phân tích từng URL, lưu vào `video-templates.md`
3. [ ] Sau 10 video: Claude tổng hợp pattern

**Không cần làm ngay:**

- Không cần script mới — `analyze-video.js` đã đủ
- Không cần database — markdown file đủ cho quy mô này
- Tổng hợp pattern làm sau khi có đủ data

---

## Lưu Ý

- Mỗi lần research có thể làm 1 URL hoặc batch 5–10 URL
- Không nhất thiết phải xem hết video mới gửi — Gemini đọc được full video
- YouTube Shorts và video dài đều phân tích được
- Facebook video URL không hỗ trợ (cần auth)
