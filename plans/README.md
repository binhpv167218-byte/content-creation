# Plans

Thư mục này chứa các kế hoạch triển khai nội dung được tạo bởi lệnh `/create-plan`.

## Cách Tạo Plan

```
/create-plan chuỗi 5 bài về [chủ đề] trong [thời gian]
```

Claude sẽ tạo file plan với tên dạng `YYYY-MM-DD-slug.md` và lưu vào đây.

## Cách Thực Thi Plan

```
/implement plans/YYYY-MM-DD-ten-plan.md
```

## Cấu Trúc Một Plan File

```markdown
# Kế Hoạch: [Tên kế hoạch]

**Ngày tạo:** DD/MM/YYYY
**Phạm vi:** [Số bài, thời gian, nền tảng]

## Tổng Quan

[Mục tiêu và phương pháp]

## Danh Sách Bài

| STT | Tiêu đề | Phương pháp | Visual | Ngày dự kiến |
| --- | ------- | ----------- | ------ | ------------ |
| 1   | ...     | ...         | ...    | ...          |

## Chi Tiết Từng Bài

[Hook, nội dung chính, visual concept cho từng bài]
```

## Ghi Chú

- Đặt tên file có ngày để giữ lịch sử theo thứ tự
- Sau khi `/implement` xong, giữ lại file plan để tham chiếu
