# Lập Kế Hoạch

Tạo một kế hoạch triển khai chi tiết cho các thay đổi trong workspace này. Kế hoạch phải là một tài liệu đầy đủ, nắm toàn bộ bối cảnh, lý do và các bước cụ thể để thực thi thay đổi một cách thống nhất với toàn dự án.

## Biến Đầu Vào

request: $ARGUMENTS (mô tả điều bạn muốn lập kế hoạch: command mới, workflow mới, thay đổi cấu trúc, cập nhật template, v.v.)

---

## Hướng Dẫn

- **QUAN TRỌNG:** Bạn đang tạo KẾ HOẠCH, không phải triển khai thay đổi. Hãy nghiên cứu kỹ, suy nghĩ kỹ rồi mới tạo tài liệu kế hoạch.
- Dùng khả năng suy luận để xem xét kỹ yêu cầu, cấu trúc workspace và cách tiếp cận phù hợp nhất.
- Nghiên cứu workspace để hiểu các pattern, convention hiện có và vị trí của thay đổi này trong toàn hệ thống.
- Tạo file kế hoạch trong thư mục `plans/` với tên: `YYYY-MM-DD-{ten-mo-ta}.md`
  - Dùng ngày hôm nay
  - Thay `{ten-mo-ta}` bằng một tên ngắn dạng kebab-case
- Điền đầy đủ mọi phần trong mẫu kế hoạch bên dưới. Thay toàn bộ `<placeholder>` bằng nội dung cụ thể, có thể hành động được.
- Hãy làm thật kỹ vì kế hoạch này sẽ được `/implement` thực thi và phải đủ rõ để không gây mơ hồ.
- Bám theo pattern sẵn có. Hãy đọc những file tương tự trong workspace trước khi đề xuất cấu trúc mới.

---

## Giai Đoạn Nghiên Cứu

Trước khi viết kế hoạch, hãy điều tra:

1. **Đọc các file tham chiếu cốt lõi:**
   - `CLAUDE.md` — tổng quan workspace
   - `context/` — bối cảnh về người dùng và dự án

2. **Khám phá những khu vực liên quan:**
   - Nếu đang tạo command: đọc các command hiện có trong `.claude/commands/`
   - Nếu đang chỉnh output: khám phá cấu trúc `outputs/` và ví dụ hiện có
   - Nếu đang cập nhật template: kiểm tra `reference/` để xem các pattern hiện tại
   - Nếu đang thêm script: rà `scripts/` để hiểu convention

3. **Hiểu các kết nối:**
   - Thay đổi này liên hệ với workflow hiện tại như thế nào?
   - Những file nào đang tham chiếu hoặc phụ thuộc vào phần sẽ bị thay đổi?
   - Có quy ước đặt tên nào cần tuân theo không?

---

## Mẫu Kế Hoạch

Hãy viết kế hoạch theo đúng cấu trúc này:

```markdown
# Kế Hoạch: <tiêu đề mô tả>

**Tạo lúc:** <YYYY-MM-DD>
**Trạng thái:** Draft
**Yêu cầu:** <tóm tắt một dòng về điều được yêu cầu>

---

## Tổng Quan

### Kế Hoạch Này Đạt Được Điều Gì

<2-3 câu mô tả kết quả cuối cùng và vì sao nó quan trọng>

### Vì Sao Điều Này Quan Trọng

<Kết nối thay đổi này với mục tiêu hoặc sứ mệnh của dự án. Nó tạo thêm giá trị như thế nào?>

---

## Trạng Thái Hiện Tại

### Cấu Trúc Liên Quan Đang Có

<Liệt kê file, thư mục hoặc pattern hiện có liên quan tới thay đổi này>

### Khoảng Trống Hoặc Vấn Đề Cần Giải Quyết

<Hiện đang thiếu gì, hỏng gì hoặc chưa tối ưu mà kế hoạch này sẽ xử lý?>

---

## Thay Đổi Đề Xuất

### Tóm Tắt Thay Đổi

<Danh sách bullet ở mức cao về toàn bộ thay đổi>

### File Mới Cần Tạo

| Đường dẫn file    | Mục đích                |
| ----------------- | ----------------------- |
| `path/to/file.md` | File này dùng để làm gì |

### File Cần Chỉnh Sửa

| Đường dẫn file    | Nội dung thay đổi    |
| ----------------- | -------------------- |
| `path/to/file.md` | Mô tả phần chỉnh sửa |

### File Cần Xóa (nếu có)

<Liệt kê các file sẽ bị xóa và lý do>

---

## Quyết Định Thiết Kế

### Các Quyết Định Chính

1. **<Quyết định>**: <Lý do>
2. **<Quyết định>**: <Lý do>

### Các Phương Án Đã Cân Nhắc

<Đã cân nhắc những cách nào khác và tại sao không chọn?>

### Câu Hỏi Mở (nếu có)

<Liệt kê những quyết định vẫn cần user trả lời trước khi triển khai>

---

## Các Bước Thực Hiện

### Bước 1: <Tên bước>

<Mô tả chi tiết việc cần làm>

**Hành động:**

- <Hành động cụ thể>

**File bị ảnh hưởng:**

- `path/to/file.md`

---

<Tiếp tục với bao nhiêu bước cũng được nếu cần>

---

## Checklist Kiểm Tra

- [ ] <Bước xác minh>
- [ ] <Bước xác minh>

---

## Tiêu Chí Thành Công

1. <Tiêu chí cụ thể, đo được>
2. <Tiêu chí cụ thể, đo được>

---

## Ghi Chú

<Bối cảnh bổ sung hoặc lưu ý cho tương lai>
```

---

## Tiêu Chuẩn Chất Lượng

- **Đầy đủ:** Mọi phần đều được điền bằng nội dung cụ thể
- **Có thể hành động:** Các bước phải đủ rõ để `/implement` chạy không cần hỏi lại
- **Nhất quán:** Bám theo pattern có sẵn của workspace
- **Rõ ràng:** Người chưa quen dự án vẫn có thể hiểu và thực hiện
- **Truy vết được:** Mọi thay đổi đều gắn lại với mục tiêu và lý do

---

## Báo Cáo

Sau khi tạo xong kế hoạch:

1. Tóm tắt ngắn kế hoạch bao gồm những gì
2. Liệt kê mọi câu hỏi mở còn cần user trả lời
3. Cung cấp full path tới file kế hoạch
4. Nhắc user chạy `/implement plans/YYYY-MM-DD-{name}.md` để thực thi
