# Kế Hoạch: Chrome Extension Bitrix24 — Auto-Sync Lead sang Airtable

**Tạo lúc:** 2026-05-28
**Trạng thái:** Draft — Chờ xác nhận 3 câu hỏi mở
**Yêu cầu:** Tạo Chrome Extension chạy trên Bitrix24 (IQI workspace, Bình là user thường không có admin) — đọc thông tin lead/deal, sync sang Airtable Khách Hàng, tự động lock responsible về Bình

---

## Tổng Quan

### Kế Hoạch Này Đạt Được Điều Gì

Khi Bình mở trang lead/deal trên Bitrix24 trong Chrome, một sidebar hiện ra cho phép sync thông tin khách sang Airtable bằng 1 click — không cần quyền admin Bitrix24, không cần Make.com, không cần server ngoài. Extension cũng tự động lock responsible = Bình trực tiếp trên trang (DOM manipulation hoặc API nếu có personal webhook).

### Vì Sao Dùng Chrome Extension Thay Vì Webhook/Make.com

Bitrix24 là workspace chung của IQI, Bình không có quyền admin nên không thể:

- Tạo outbound webhook (cần admin)
- Cài app từ Bitrix24 marketplace (cần admin approve)
- Truy cập REST API với scope rộng (giới hạn bởi role)

Chrome Extension chạy hoàn toàn client-side trong browser của Bình — không cần bất kỳ quyền nào từ IQI, không ảnh hưởng đến workspace chung.

---

## Kiến Trúc

```
Bình mở trang Lead/Deal trên Bitrix24 (Chrome)
        ↓
Content Script phát hiện URL pattern (/crm/lead/ hoặc /crm/deal/)
        ↓
Đọc thông tin từ DOM (tên, SĐT, stage, ngày tạo, dự án)
        ↓
Sidebar hiện ra với nút "Sync sang Airtable" + "Lock cho mình"
        ↓ ↓
Background Service Worker    DOM Manipulation
→ POST Airtable API          → Click "Assign to me" / đổi Responsible
  (upsert Khách Hàng)          trực tiếp trên trang Bitrix24
```

### Không Cần Local Server

Khác Zalo extension (phải gọi AI Gemini nên cần Python server), Bitrix24 extension đơn giản hơn:

- Chỉ cần đọc DOM + gọi Airtable API
- Background service worker của Extension MV3 có thể call HTTPS API trực tiếp
- Không cần `server.py`, không cần Mac giữ process

### Cấu Trúc Thư Mục

```
scripts/bitrix24-extension/
├── manifest.json          # MV3, host_permissions cho Bitrix24 domain + api.airtable.com
├── content.js             # Đọc DOM Bitrix24, inject sidebar
├── background.js          # Service worker — gọi Airtable API
├── sidebar.css            # Style sidebar (copy/adapt từ Zalo extension)
├── icon48.png
└── icon128.png
```

---

## Trạng Thái Hiện Tại

### Cấu Trúc Liên Quan Đang Có

- `scripts/zalo-extension/` — Chrome Extension MV3 hoàn chỉnh, cùng pattern sẽ follow
- `scripts/airtable_sync.py` — biết field schema bảng Khách Hàng `tbl8hbsOvV2y2MnfN`
- `.env` — đã có `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`

### Khoảng Trống Cần Giải Quyết

- Chưa biết URL pattern chính xác của Bitrix24 IQI (domain công ty)
- Chưa biết DOM structure trang lead/deal của Bitrix24
- Airtable credentials cần embed vào extension (hoặc user input lần đầu)

---

## Field Mapping: Bitrix24 DOM → Airtable

| Thông tin        | Lấy từ Bitrix24                | Airtable field                |
| ---------------- | ------------------------------ | ----------------------------- |
| Tên khách        | DOM selector tên lead/deal     | `Tên`                         |
| Số điện thoại    | DOM selector phone field       | `Số điện thoại` (upsert key)  |
| Dự án quan tâm   | DOM selector category/type     | `Dự án quan tâm`              |
| Stage/trạng thái | DOM selector stage bar         | `Phase` (map sang A-F)        |
| Nguồn lead       | DOM selector source field      | `Nguồn`                       |
| Ghi chú          | DOM selector comment/note      | `Nội dung tương tác gần nhất` |
| Bitrix24 ID      | URL (`/crm/lead/details/123/`) | `Bitrix24 ID` (field mới)     |
| Ngày tạo         | DOM hoặc URL timestamp         | `Ngày liên hệ đầu`            |

_Selector chính xác xác định sau khi inspect DOM thực tế._

---

## Câu Hỏi Mở — Phải Trả Lời Trước Khi Implement

**1. Domain Bitrix24 của IQI là gì?**
Ví dụ: `iqi.bitrix24.vn` hay `iqivietnam.bitrix24.com`?
Cần để set `host_permissions` trong manifest.json đúng domain.

**2. Bitrix24 IQI dùng module Lead hay Deal?**

- **Lead** (`/crm/lead/details/123/`) — khách chưa qualify
- **Deal** (`/crm/deal/details/123/`) — khách đang xử lý

Hoặc cả hai? Extension sẽ detect cả hai nếu cần.

**3. Bình muốn sync thủ công (nhấn nút) hay tự động khi mở trang?**

- **Thủ công (khuyến nghị):** Sidebar hiện, Bình review rồi nhấn "Sync" — kiểm soát được
- **Tự động:** Mỗi khi mở trang lead → tự sync luôn — nhanh nhưng có thể tạo bản ghi rác

---

## Các Bước Thực Hiện

### Bước 1: Xác Nhận 3 Câu Hỏi Mở

Bình trả lời 3 câu hỏi trên. Đặc biệt câu 1 (domain) là bắt buộc để viết manifest.json đúng.

---

### Bước 2: Inspect DOM Bitrix24

Mở trang lead/deal trên Bitrix24, dùng Chrome DevTools để tìm:

- Selector của tên, SĐT, stage, source, ghi chú
- URL pattern chính xác

Bước này cần Bình chụp màn hình hoặc share HTML snippet. Extension sẽ dựa vào selector này để đọc data.

**Hành động:** Bình mở 1 trang lead, bấm F12, copy selector của từng field. Mình sẽ viết selector dựa trên đó.

---

### Bước 3: Tạo Extension

Tạo `scripts/bitrix24-extension/` với 4 file chính:

**`manifest.json`:**

```json
{
  "manifest_version": 3,
  "name": "Bitrix24 → Airtable Sync",
  "version": "1.0",
  "permissions": ["activeTab", "scripting", "storage"],
  "host_permissions": [
    "https://*.bitrix24.vn/*",
    "https://*.bitrix24.com/*",
    "https://api.airtable.com/*"
  ],
  "content_scripts": [
    {
      "matches": [
        "https://*.bitrix24.vn/crm/*",
        "https://*.bitrix24.com/crm/*"
      ],
      "js": ["content.js"],
      "css": ["sidebar.css"],
      "run_at": "document_idle"
    }
  ],
  "background": { "service_worker": "background.js" }
}
```

**`content.js`** — logic chính:

- Detect URL change (SPA, dùng `MutationObserver` hoặc `setInterval` check URL)
- Khi URL khớp `/crm/lead/details/` hoặc `/crm/deal/details/` → parse DOM
- Inject sidebar với: thông tin đọc được + nút "Sync Airtable" + nút "Lock cho mình"
- Gửi message tới background.js khi Bình nhấn nút

**`background.js`** — gọi API:

- Nhận message từ content.js
- `fetch()` POST/PATCH lên Airtable API (upsert theo SĐT)
- Trả kết quả về content.js để hiện thông báo

**Airtable credentials:** Lần đầu cài extension, popup nhỏ để Bình nhập API key + Base ID → lưu vào `chrome.storage.local`. Không hardcode trong source.

---

### Bước 4: Logic Lock Responsible

Có 2 cách, dùng cách nào phụ thuộc vào quyền Bình có trên Bitrix24:

**Cách A — DOM Manipulation (không cần API, luôn dùng được):**

- Extension tìm dropdown "Người chịu trách nhiệm" trên trang
- Tự động set = Bình (theo tên/ID đã config sẵn)
- Simulate click như người dùng thật

**Cách B — Personal Webhook (nếu Bitrix24 IQI cho phép user tạo):**

- Bitrix24 → Cài đặt → Developer → Inbound webhook (personal, không cần admin)
- Extension gọi `GET /rest/USER_ID/TOKEN/crm.lead.update.json` để set responsible
- Nhanh và đáng tin cậy hơn DOM manipulation

Mình sẽ implement Cách A trước (luôn hoạt động), thêm Cách B nếu cần.

---

### Bước 5: Thêm Field `Bitrix24 ID` vào Airtable

Thêm field text mới tên `Bitrix24 ID` vào bảng Khách Hàng — dùng làm key phụ để update đúng record khi lead đã có trong Airtable.

**Hành động:** Mình tạo field qua Airtable API hoặc hướng dẫn Bình thêm thủ công (30 giây trong UI).

---

### Bước 6: Cài Extension vào Chrome

```
Chrome → Settings → Extensions → Developer mode ON
→ Load unpacked → chọn thư mục scripts/bitrix24-extension/
```

Test trên 1 lead thật: mở trang, sidebar xuất hiện, nhấn Sync → kiểm tra Airtable.

---

### Bước 7: Cập Nhật Tài Liệu

- Thêm Bitrix24 Extension vào phần Tools & APIs trong `CLAUDE.md`
- Tạo `context/bitrix24-setup.md` — ghi domain, field mapping, selector đã dùng

---

## Checklist Kiểm Tra

- [ ] Extension load không lỗi trong Chrome DevTools
- [ ] Sidebar xuất hiện khi mở trang lead/deal Bitrix24
- [ ] Tên, SĐT đọc đúng từ DOM
- [ ] Nhấn "Sync" → record xuất hiện/cập nhật trong Airtable Khách Hàng
- [ ] Không tạo record trùng nếu sync cùng 1 lead 2 lần
- [ ] Nút "Lock cho mình" → Responsible đổi về Bình trên trang
- [ ] Airtable credentials lưu được qua `chrome.storage.local`

---

## Tiêu Chí Thành Công

1. Mở trang lead bất kỳ → sidebar xuất hiện trong 2 giây
2. Nhấn "Sync" → Airtable có record trong vòng 5 giây
3. Không cần bất kỳ quyền admin Bitrix24 nào
4. Hoạt động offline với Airtable (chỉ cần internet, không cần local server)

---

## Ghi Chú

- Extension chạy hoàn toàn trong browser — không ảnh hưởng Bitrix24 workspace của IQI, không ai biết Bình đang dùng tool này
- Bitrix24 là SPA (React-based) — DOM thay đổi động. Content script cần `MutationObserver` để detect khi trang lead load xong, không chỉ dùng `DOMContentLoaded`
- Nếu Bitrix24 IQI update giao diện thì selector có thể cần cập nhật — ghi lại selector trong `context/bitrix24-setup.md` để dễ fix sau
- Pattern này có thể mở rộng: thêm nút "Tạo nhắc follow-up" ghi vào Airtable field `Ngày follow-up` mà không cần mở Airtable thủ công
