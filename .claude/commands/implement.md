# Triển Khai

Thực thi một kế hoạch đã được tạo bởi `/create-plan`. Đọc kỹ kế hoạch, làm từng bước theo đúng thứ tự và báo cáo lại phần công việc đã hoàn thành.

## Biến Đầu Vào

plan_path: $ARGUMENTS (đường dẫn tới file kế hoạch, ví dụ `plans/2026-01-28-add-guest-research-command.md`)

---

## Hướng Dẫn

### Giai Đoạn 1: Hiểu Kế Hoạch

1. **Đọc toàn bộ file kế hoạch.** Không được lướt qua.
2. **Kiểm tra điều kiện tiên quyết:**
   - Có câu hỏi mở nào cần được trả lời trước khi triển khai không?
   - Có phụ thuộc vào tài nguyên ngoài hay quyết định từ user không?
   - Nếu có blocker, dừng lại và hỏi user.
3. **Xác nhận kế hoạch đã sẵn sàng:**
   - Trạng thái phải là `Draft` hoặc `Ready`
   - Tất cả các phần phải đã được điền đầy đủ

---

### Giai Đoạn 2: Thực Thi Kế Hoạch

1. **Làm theo phần Step-by-Step Tasks đúng thứ tự.**
   - Hoàn thành trọn vẹn từng bước rồi mới sang bước tiếp theo
   - Nếu một bước yêu cầu tạo file, hãy tạo file hoàn chỉnh chứ không tạo stub
   - Nếu một bước yêu cầu sửa file, hãy đọc file trước rồi chỉnh chính xác

2. **Với mỗi task:**
   - Đọc những file bị ảnh hưởng
   - Thực hiện thay đổi đã nêu
   - Tự kiểm tra thay đổi trước khi tiếp tục

3. **Xử lý vấn đề một cách hợp lý:**
   - Nếu không thể làm đúng như kế hoạch, ghi rõ vấn đề và thích nghi nếu ý định vẫn rõ
   - Nếu không chắc nên làm gì, hỏi user thay vì đoán
   - Ghi nhận mọi điểm lệch so với kế hoạch

---

### Giai Đoạn 3: Kiểm Tra

1. **Chạy qua Validation Checklist** trong kế hoạch
2. **Kiểm tra Success Criteria** đã đạt hay chưa
3. **Rà soát cross-reference và độ nhất quán:**
   - Đảm bảo file mới được tham chiếu ở đúng nơi cần thiết
   - Kiểm tra xem `CLAUDE.md` có cần cập nhật nếu cấu trúc workspace thay đổi không

---

### Giai Đoạn 4: Cập Nhật Trạng Thái Kế Hoạch

Sau khi triển khai xong, cập nhật lại file kế hoạch:

1. Đổi `**Status:** Draft` thành `**Status:** Implemented`
2. Thêm phần `Implementation Notes` ở cuối:

```markdown
---

## Implementation Notes

**Implemented:** <YYYY-MM-DD>

### Summary

<Tóm tắt ngắn điều đã làm>

### Deviations from Plan

<Liệt kê mọi thay đổi khác với kế hoạch, hoặc "None">

### Issues Encountered

<Liệt kê mọi vấn đề gặp phải và cách xử lý, hoặc "None">
```

---

## Báo Cáo

Sau khi triển khai, hãy cung cấp:

1. **Tóm tắt:** Danh sách bullet các phần việc đã hoàn thành
2. **Các file đã thay đổi:** Liệt kê tất cả file tạo mới, sửa hoặc xóa
3. **Kết quả kiểm tra:** Trạng thái của từng mục trong checklist
4. **Điểm lệch:** Những chỗ khác với kế hoạch ban đầu
5. **Bước tiếp theo:** Mọi việc follow-up còn cần làm
