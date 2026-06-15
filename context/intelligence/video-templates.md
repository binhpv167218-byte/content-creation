# Video Style Templates

Phân tích từ clip thật, dùng làm tham chiếu cho pipeline auto-edit.

---

## Template 1: Storytelling (manhvibe style)

**Nguồn:** @manhvibe TikTok — 611 likes, 76 saves
**Tool gốc:** CapCut
**Dài:** ~75 giây
**Dùng cho:** Bài chia sẻ kinh nghiệm nghề, bài học cá nhân, góc nhìn thị trường

---

### Cấu trúc video

```
[0-3s]   HOOK FRAME — cảnh mở, chữ to 3 dòng hierarchy
[3-20s]  THIẾT LẬP VẤN ĐỀ — close-up, caption nhỏ giữa, narration
[20-40s] B-ROLL + QUOTE — cảnh B&W hoặc cảnh thiên nhiên + câu trích dẫn
[40-60s] BÀI HỌC — tiếp tục narration + cảnh hỗ trợ
[60-75s] KẾT — quay lại cảnh mở đầu (circular structure), câu kết
```

---

### Typography System

**Hook text (giây đầu tiên):**

- Dòng 1: Font size ~96px, Bold, White — từ khoá chính (VD: "Thất bại")
- Dòng 2: Font size ~52px, Regular, White — câu bổ nghĩa
- Dòng 3: Font size ~64px, Bold Italic, White — câu kết hook
- Alignment: Center
- Vị trí: Giữa màn hình, hơi lên trên center (40-50% từ top)

**Body captions (suốt video):**

- Font size: ~44px
- Weight: Regular hoặc Light
- Color: White thuần (#FFFFFF)
- Alignment: Center
- Vị trí: Center vertical (không phải bottom lower third)
- Không có background/box — chữ nổi trực tiếp trên video
- Mỗi caption: 4-7 từ, ngắt dòng tạo nhịp đọc

---

### Footage Types

1. **Cảnh contemplative** (chiếm 40%): Người đứng lưng camera, nhìn ra biển/cảnh quan — mood suy nghĩ
2. **Close-up face** (20%): Góc thấp ngước lên, ánh sáng tối — cảm xúc sâu
3. **B&W archival** (20%): Clip người nổi tiếng, cảnh lịch sử — tạo chiều sâu
4. **Landscape** (20%): Hoàng hôn, biển, thiên nhiên — emotional backdrop

**Cho Bình Phan:** thay bằng cảnh Đà Nẵng — biển Mỹ Khê, cầu Rồng, dự án đang xây, hoàng hôn Non Nước

---

### Color Grading

- **Cảnh cá nhân:** Warm golden — tăng orange/amber, giảm blue, shadow đậm
- **B&W clips:** Desaturate hoàn toàn, tăng contrast, vignette nhẹ
- **Không dùng filter quá mạnh** — natural nhưng cinematic

FFmpeg filter cho warm storytelling grade:

```
eq=saturation=0.85:contrast=1.05:brightness=-0.03,
curves=r='0/0 0.5/0.58 1/1':g='0/0 0.5/0.5 1/0.92':b='0/0 0.5/0.42 1/0.88'
```

---

### Audio

- Voiceover narration (giọng chính, không có âm gốc từ clip)
- Nhạc nền: instrumental lo-fi hoặc piano nhẹ, volume ~15%
- Không có SFX transition — im lặng và nhạc nền đủ

---

### Caption Writing Style (Claude prompt)

```
Viết captions theo style storytelling manhvibe:
- Ngắt thành các đoạn 4-7 từ, mỗi đoạn 2-4 giây
- Không dùng bullet, không dùng emoji trong caption
- Câu phải tự đứng được — người xem mute vẫn hiểu ý
- Nhịp điệu: ngắn — dừng — tiếp — dừng (như đọc thơ)
- Hook dòng đầu phải gây tò mò hoặc bất ngờ
```

---

### Circular Structure (đặc trưng)

Cảnh cuối = cảnh đầu → tạo cảm giác bài học đã được "đóng lại" hoàn chỉnh.
Claude nên đề xuất dùng clip đầu tiên lặp lại ở cuối với caption khác đi.

---

## Template 2: Dự án BDS (quangsonrealestate style)

**Nguồn:** @quangsonrealestate183 TikTok
**Dùng cho:** Bài giới thiệu dự án, phân tích thị trường, so sánh BDS

---

### Cấu trúc video

```
[0-2s]   TITLE CARD — chữ to + từ khoá màu accent trên nền presenter toàn thân
[2-15s]  HOOK NÓI THẲNG — câu hỏi hoặc statement mạnh, caption kiểu "anh chị..."
[15-40s] NỘI DUNG CHÍNH — presenter + virtual background CGI project
[40-55s] DỮ LIỆU/SỐ LIỆU — motion graphics: giá, diện tích, tiến độ
[55-60s] CTA — "Nhắn mình nếu anh chị quan tâm"
```

---

### Typography System

**Title card (2 giây đầu):**

- Từ khoá chính: Bold, size lớn, màu accent (xanh lá gốc → dùng cam #f5a050 cho Bình)
- Text phụ: Regular white, nhỏ hơn 40%
- Vị trí: Giữa màn hình, overlay lên presenter

**Body captions:**

- Style conversational: "anh chị quan tâm... BĐS khu vực này..."
- Dùng `...` để tạo suspense
- Font white, nhỏ, không bold
- Vị trí: Center hoặc lower-center

---

### Caption Writing Style (Claude prompt)

```
Viết captions theo style BDS hook:
- Mở đầu bằng câu hỏi kéo khán giả vào: "Anh chị có biết..."
- Dùng "..." để tạo nhịp dừng
- Số liệu cụ thể: giá, %, m², năm
- Kết bằng CTA rõ ràng: "Nhắn Bình nếu..."
```

---

## Áp dụng vào Pipeline

Khi Claude nhận ý tưởng video, xác định style trước:

- "storytelling / kinh nghiệm / bài học nghề" → dùng Template 1
- "dự án / thị trường / số liệu" → dùng Template 2

Thêm vào analyze prompt: `video_style: storytelling | project`
