---
name: gmail-label
description: Đọc và phân loại email trong Gmail inbox, tự động gán nhãn theo hệ thống phân loại. Use when asked to "label emails", "classify emails", "phân loại email", "gán nhãn email", "dọn inbox", "organize inbox", "sort emails", "đọc email", "check email", or any request to read/classify/label Gmail messages. Supports custom count (e.g., "label 50 emails", "phân loại 200 email").
---

# Gmail Label — Phân Loại & Gán Nhãn Email Tự Động

Đọc N email gần nhất trong inbox, phân loại bằng Python regex script, và gán label tự động qua Gmail API.

## Hệ Thống Nhãn

7 nhãn phân loại — mỗi email thuộc đúng 1 nhãn:

| Label ID  | Tên               | Quy tắc phân loại                                                                                                                                                                                                                                                                                                   |
| --------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Label_1` | **AI Newsletter** | Bản tin AI/tech, substacks về AI/tech/startup/productivity, tech creator emails. Nhận dạng qua sender domain: substack.com, beehiiv.com, tldrnewsletter.com, therundown.ai, joinsuperhuman.ai, practicaly.ai, neatprompts.com, theneurondaily.com, deeplearning.ai, every.to, và các newsletter tương tự về AI/tech |
| `Label_2` | **Skool/Revenue** | Subject chứa "New customer:" hoặc "Member upgrade:" từ noreply@skool.com                                                                                                                                                                                                                                            |
| `Label_3` | **Skool/Message** | Subject chứa "sent you a message" từ Skool, hoặc email cá nhân trực tiếp gửi nội dung/ý tưởng                                                                                                                                                                                                                       |
| `Label_4` | **Skool/Digest**  | Subject chứa "Weekly digest", "notification since", "event happening" hoặc "posted" từ Skool; Substack note digests                                                                                                                                                                                                 |
| `Label_5` | **Orders**        | From notification@ladipage.net (đơn hàng LadiSales)                                                                                                                                                                                                                                                                 |
| `Label_6` | **Promotions**    | Mua sắm, giải trí, crypto exchange, fitness, ngân hàng, social media suggestions, dược phẩm, gaming, tiện ích, cập nhật sản phẩm non-AI, hóa đơn điện tử                                                                                                                                                            |
| `Label_7` | **Security**      | Cảnh báo bảo mật, cập nhật chính sách từ Google, GitHub, Facebook/Meta                                                                                                                                                                                                                                              |

### Quy Tắc Ưu Tiên

1. **Security** — luôn ưu tiên cao nhất
2. **Orders** — nhận dạng rõ ràng qua sender
3. **Skool/Revenue** — nhận dạng rõ ràng qua subject pattern
4. **Skool/Message** — nhận dạng rõ ràng qua subject pattern
5. **Skool/Digest** — nhận dạng rõ ràng qua subject pattern
6. **AI Newsletter** — nhận dạng qua sender domain
7. **Promotions** — mặc định cho email thương mại còn lại

## Quy Trình Thực Hiện

### Bước 1: Đảm Bảo Labels Tồn Tại + Fetch Emails (SONG SONG)

Gọi **đồng thời** trong cùng 1 message:

- `mcp__gmail__get_or_create_label` cho tất cả 7 nhãn
- `mcp__gmail__search_emails` với query `in:inbox` và maxResults = N

Tổng cộng: 8 API calls song song trong 1 roundtrip.

```
AI Newsletter
Skool/Revenue
Skool/Message
Skool/Digest
Orders
Promotions
Security
```

### Bước 2: Phân Loại Bằng Python Script

**KHÔNG phân loại bằng LLM.** Dùng script `classify-emails.py` để pattern match trong milliseconds.

Khi `search_emails` trả kết quả trực tiếp (< vài trăm email):

1. Lưu output vào file tạm
2. Chạy script:

```bash
python3 scripts/classify-emails.py <input_file> --output outputs/classified.json
```

Khi kết quả quá lớn và được lưu tự động vào file (MCP tool result):

```bash
python3 scripts/classify-emails.py <tool-result-file-path> --output outputs/classified.json
```

Script sẽ output JSON:

```json
{
  "total": 500,
  "labels": {
    "Label_1": ["id1", "id2", ...],
    "Label_2": ["id3", ...],
    ...
  },
  "summary": [
    {"label_id": "Label_1", "name": "AI Newsletter", "count": 209, "examples": ["..."]},
    ...
  ]
}
```

### Bước 3: Gán Nhãn Theo Batch

Đọc `outputs/classified.json`, rồi gọi `mcp__gmail__batch_modify_emails` **song song** cho tất cả labels có email:

```
mcp__gmail__batch_modify_emails({
  messageIds: [...ids từ classified.json],
  addLabelIds: ["Label_X"]
})
```

Tối đa 7 calls song song, 1 roundtrip.

### Bước 4: Báo Cáo

Trình bày kết quả từ `classified.json`:

```markdown
## Kết Quả Phân Loại Email

| Nhãn          | Số lượng | Ví dụ                           |
| ------------- | -------- | ------------------------------- |
| AI Newsletter | XX       | TLDR AI, The Neuron, ...        |
| Skool/Revenue | XX       | New customer: ...               |
| Skool/Message | XX       | [Tên] sent you a message        |
| Skool/Digest  | XX       | Weekly digest ...               |
| Orders        | XX       | DH1234, DH1235, ...             |
| Promotions    | XX       | Shopee, Netflix, ...            |
| Security      | XX       | Google alert, GitHub policy ... |
| **Tổng**      | **XX**   |                                 |
```

Nếu có email đáng chú ý (cần phản hồi gấp, tin nhắn cá nhân, cảnh báo bảo mật), highlight riêng ở đầu.

## Tùy Chỉnh

### Thêm Nhãn Mới

Khi user yêu cầu thêm nhãn, cập nhật **cả hai nơi**:

1. Bảng hệ thống nhãn ở trên
2. Rules trong `scripts/classify-emails.py`

### Custom Query

User có thể chỉ định query khác ngoài `in:inbox`:

- `"label 50 email chưa đọc"` → query: `in:inbox is:unread`, maxResults: 50
- `"phân loại email tuần này"` → query: `in:inbox newer_than:7d`
- `"dọn email từ newsletter"` → query: `in:inbox from:substack.com OR from:beehiiv.com`

### Cập Nhật Classification Rules

Quy tắc phân loại nằm trong `scripts/classify-emails.py`. Để thêm sender domain mới cho AI Newsletter, thêm vào list `AI_NEWSLETTER_DOMAINS`. Để thêm label mới, thêm logic vào function `classify_email()`.

## Hiệu Suất

- **3 roundtrip tổng cộng**: (1) fetch + create labels, (2) classify bằng Python, (3) batch label
- Phân loại 500 email: ~50ms (Python regex, không cần LLM)
- Batch modify: 7 API calls song song
- **Tổng thời gian dự kiến: 30-60 giây** cho bất kỳ số lượng email nào (bottleneck là Gmail API, không phải phân loại)
