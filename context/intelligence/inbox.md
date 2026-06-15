# Content Inbox — Nguồn Ý Tưởng

> **Cách dùng:** Paste link hoặc raw text vào section PENDING bên dưới.
> Nhắn Claude "phân tích inbox" hoặc chạy `/analyze-inbox` để xử lý.
>
> **Tool routing tự động:**
>
> - Bài báo (vnexpress, cafef, tuoitre, batdongsan...) → Perplexity (`research_bot.py`)
> - YouTube URL → Gemini (`analyze-video.js`)
> - TikTok URL → Apify (`clockworks/free-tiktok-scraper`)
> - Facebook URL → thường bị login wall, ghi chú raw text
> - Raw text / ghi chú → Claude phân tích trực tiếp
>
> **Sau khi dùng entry để tạo content:** Đổi `Status: PENDING` → `Status: [USED: post-NNN]`
> Giữ lại entry, không xóa. Khi scan sẽ bỏ qua entries đã [USED].
> Tối đa 50 entries tổng. Entries cũ nhất và đã [USED] xóa khi vượt giới hạn.

---

## PENDING — Chờ Phân Tích

_Paste link hoặc text vào đây. Claude sẽ xử lý khi được gọi._

---

## Thị Trường

_Entries về giá, xu hướng, chính sách BĐS Đà Nẵng và cả nước_

### Đà Nẵng Chấp Thuận 2 Dự Án Hạ Tầng Khu Thương Mại Tự Do, Vốn 13.400 Tỷ

**Nguồn:** https://www.danang.gov.vn/vi/web/dng/w/chap-thuan-chu-truong-dau-tu-02-du-an-ha-tang-khu-chuc-nang-tai-khu-thuong-mai-tu-do-voi-von-dang-ky-hon-13400-ty-dong | **Tên nguồn:** Cổng TTĐT Đà Nẵng | **Thêm:** 2026-06-12 | **Status:** PENDING
**Tags:** #thị-trường #video #carousel #ảnh

**Tóm tắt:**
UBND TP Đà Nẵng vừa chấp thuận chủ trương đầu tư 2 dự án hạ tầng khu chức năng trong Khu Thương Mại Tự Do Đà Nẵng, tổng vốn đăng ký hơn 13.400 tỷ đồng. Đây là hạ tầng kỹ thuật (logistics, kho bãi, giao thông nội khu) chứ không phải BĐS nhà ở để bán lẻ. Khu TMTD gắn với cảng biển và hoạt động xuất nhập khẩu. Hiện mới ở giai đoạn chủ trương, chưa mở bán sản phẩm BĐS nào.

**Data/Quotes:**

- Tổng vốn đăng ký: hơn 13.400 tỷ đồng cho 02 dự án hạ tầng (nguồn: Cổng TTĐT Đà Nẵng)
- Cơ quan phê duyệt: UBND TP Đà Nẵng
- Tính chất: hạ tầng logistics, kho bãi, giao thông nội khu. Không phải nhà ở, không có sổ từng lô cho khách lẻ
- Giai đoạn: chủ trương đầu tư. Còn phải qua: chuẩn bị dự án, phê duyệt, thiết kế, đấu thầu trước khi xây dựng

**Hook ideas:**

1. "13.400 tỷ vừa được bật đèn xanh đổ vào Khu Thương Mại Tự Do Đà Nẵng. Với BĐS xung quanh, điều này có nghĩa gì?" (carousel/ảnh)
2. "Đà Nẵng đang xây gì tiếp theo sau sân bay và bến du thuyền?" (video market, ghép vào series hạ tầng)
3. "Khu Thương Mại Tự Do không phải BĐS nhà ở. Nhưng nó kéo theo thứ gì cho người mua căn hộ gần đó?" (ảnh cá nhân, góc nhìn phân tích)

### Đà Nẵng Khảo Sát Nhu Cầu Thuê, Mua Nhà Ở Xã Hội Tháng 6/2026

**Nguồn:** https://www.danang.gov.vn/vi/web/dng/w/tu-ngay-01-6-den-30-6-khao-sat-nhu-cau-thue-mua-nha-o-xa-hoi | **Tên nguồn:** Cổng TTĐT Đà Nẵng | **Thêm:** 2026-06-12 | **Status:** PENDING
**Tags:** #thị-trường #ảnh #carousel

**Tóm tắt:**
Sở Xây dựng Đà Nẵng tổ chức khảo sát nhu cầu thuê và mua nhà ở xã hội từ 01/6 đến 30/6/2026, bao gồm cả nhà lưu trú công nhân khu công nghiệp. Đây là đợt thu thập nhu cầu, chưa phải mở bán dự án cụ thể. Chưa có thông tin tên dự án, địa điểm hay điều kiện đăng ký.

**Data/Quotes:**

- Thời gian khảo sát: 01/6 đến 30/6/2026 (nguồn: Cổng TTĐT Đà Nẵng)
- Cơ quan thực hiện: Sở Xây dựng Đà Nẵng
- Phạm vi: nhà ở xã hội + nhà lưu trú công nhân khu công nghiệp

**Hook ideas:**

1. "Đà Nẵng đang hỏi xem có bao nhiêu người cần nhà ở xã hội. Câu hỏi đó tiết lộ điều gì về thị trường?" (ảnh cá nhân, góc nhìn phân tích)
2. "Nhà ở xã hội Đà Nẵng: cầu đang lớn hơn cung rất nhiều. Với người có tiền, phân khúc thay thế là căn hộ thương mại giá vừa." (carousel thị trường)
3. "Mình hay nhận câu hỏi: có nhà ở xã hội gần trung tâm Đà Nẵng không? Câu trả lời ngắn là: chưa đủ." (ảnh cá nhân, storytelling)

### Đà Nẵng Rút Ngắn 5 Thủ Tục Đất Đai Xuống Còn 15 Ngày Làm Việc

**Nguồn:** https://www.danang.gov.vn/vi/web/dng/w/rut-ngan-thoi-gian-giai-quyet-05-thu-tuc-hanh-chinh-linh-vuc-dat-dai-xuong-con-15-ngay-lam-viec-1 | **Tên nguồn:** Cổng TTĐT Đà Nẵng | **Thêm:** 2026-06-12 | **Status:** PENDING
**Tags:** #thị-trường #pháp-lý #ảnh #carousel

**Tóm tắt:**
UBND TP Đà Nẵng rút ngắn 5 thủ tục hành chính đất đai xuống tối đa 15 ngày làm việc, áp dụng tại UBND quận/huyện và Văn phòng Đăng ký đất đai. 5 thủ tục gồm: cấp sổ lần đầu, sang tên (chuyển nhượng/tặng cho/thừa kế), tách thửa/hợp thửa, thế chấp/xóa thế chấp, chỉnh lý/cấp đổi sổ. Trước đây mỗi thủ tục mất 20-30 ngày. Áp dụng cho hộ gia đình, cá nhân. Ý nghĩa thực tế: sang tên nhanh hơn, ít rủi ro kẹt sổ, ngân hàng giải ngân nhanh hơn.

**Data/Quotes:**

- 5 thủ tục, rút ngắn còn 15 ngày làm việc, giảm 3-7 ngày so với trước (nguồn: Cổng TTĐT Đà Nẵng)
- Áp dụng cho hộ gia đình, cá nhân. Tổ chức/dự án có thủ tục riêng
- Lợi ích: sang tên nhanh, ít kẹt sổ, ngân hàng giải ngân hồ sơ thế chấp BĐS nhanh hơn

**Hook ideas:**

1. "Sang tên nhà ở Đà Nẵng giờ còn 15 ngày. Trước đây mất 20-30 ngày. Mình hay gặp khách lo kẹt sổ: thông tin này giải quyết đúng nỗi lo đó." (ảnh cá nhân, storytelling)
2. "5 thủ tục đất đai Đà Nẵng vừa được rút ngắn. Mua bán căn hộ 2026 thực tế thay đổi gì?" (carousel thị trường)
3. "Đà Nẵng đang dọn đường cho giao dịch BĐS minh bạch và nhanh hơn. Người mua được lợi gì?" (video market)

### Lễ Hội Tận Hưởng Đà Nẵng 2026 + DIFF 2026 — Lịch Sự Kiện Mùa Hè

**Nguồn:** https://www.danang.gov.vn/vi/web/dng/w/infographic-le-hoi-tan-huong-da-nang-2026 | **Tên nguồn:** Cổng TTĐT Đà Nẵng | **Thêm:** 2026-06-12 | **Status:** PENDING
**Tags:** #thị-trường #du-lịch #video #ảnh #carousel

**Tóm tắt:**
DIFF 2026 chạy từ 30/5 đến 11/7/2026 với 6 đêm pháo hoa tại Cảng sông Hàn, chủ đề "United Horizons". Lễ hội Tận Hưởng Đà Nẵng 2026 diễn ra 22-26/7/2026 tại Công viên Biển Đông, chủ đề "Đà Nẵng - Chạm về nguyên bản". Hai sự kiện nối tiếp nhau tạo thành mùa hè du lịch đặc biệt. Đây là dữ liệu hỗ trợ luận điểm cho thuê ngắn ngày cao điểm và giá trị view biển/sông Hàn của căn hộ.

**Data/Quotes:**

- DIFF 2026: 6 đêm pháo hoa, 30/5 đến 11/7/2026, địa điểm: Cảng sông Hàn (nguồn: Cổng TTĐT Đà Nẵng + danago.vn)
- Lịch: 30/5 khai mạc, 6/6, 13/6, 20/6, 27/6, 11/7 chung kết. Mỗi đêm 20 phút
- Lễ hội Tận Hưởng: 22-26/7/2026, Công viên Biển Đông, lễ khai mạc tối 23/7
- Hoạt động: yoga bình minh, EDM bãi biển, phim ngoài trời, diều LED, thể thao biển

**Hook ideas:**

1. "DIFF 2026 có 6 đêm pháo hoa từ 30/5 đến 11/7. Căn hộ trực diện sông Hàn mùa này: cho thuê ngắn ngày hay ở tự trải nghiệm?" (ảnh cá nhân, liên kết Symphony 5)
2. "Đà Nẵng mùa hè 2026: DIFF kết thúc, Tận Hưởng bắt đầu ngay. Từ 30/5 đến 26/7 thành phố không ngủ. Đây là thứ nhà đầu tư cho thuê tính vào dòng tiền." (carousel/video thị trường)
3. "Khách hỏi mình: mua căn hộ Đà Nẵng để cho thuê, mùa cao điểm là lúc nào? Mình chỉ vào lịch: DIFF tháng 5-7, Tận Hưởng tháng 7. Gần 3 tháng liên tiếp." (ảnh cá nhân)

### Hạ Tầng Đô Thị Tiếp Sức BĐS Đà Nẵng — Sân Bay, Đường Sắt, Nam ĐN

**Nguồn:** VnExpress (vnexpress.net) + Thời báo Tài chính VN | **Tên nguồn:** VnExpress + Thời báo TCVN | **Thêm:** 2026-06-12 | **Status:** PENDING
**Tags:** #thị-trường #hạ-tầng #video #carousel

**Tóm tắt:**
4 tháng đầu 2026, Đà Nẵng đón 6 triệu lượt khách, tăng 19% — du lịch và hạ tầng được môi giới đánh giá đang tiếp sức cho BĐS. Đường sắt đô thị số 2 Đà Nẵng-Hội An-Chu Lai: tổng 103km, vốn 265.972 tỷ, giai đoạn 1 (30km, 14 ga, ĐN-Hội An) dự kiến khởi công 2/2027, vận hành 2032. Chủ đầu tư: THACO (Đại Quang Minh). Nam ĐN (Ngũ Hành Sơn, Điện Ngọc) và trục ĐN-Hội An sẽ hưởng lợi trực tiếp khi nhà ga được chốt vị trí.

**Data/Quotes:**

- 6 triệu lượt khách 4T đầu 2026, tăng 19% (nguồn: VnExpress)
- Đường sắt đô thị số 2: 103km, 265.972 tỷ đồng, giai đoạn 1 ĐN-Hội An 30km/14 ga (nguồn: Thời báo TCVN)
- Dự kiến khởi công 2/2027, vận hành tuyến đầu 2032 nếu được phê duyệt
- BĐS dọc sông Cổ Cò, Điện Ngọc, Nam Ngũ Hành Sơn hưởng lợi trực tiếp

**Hook ideas:**

1. "Đường sắt ĐN-Hội An 103km, dự kiến chạy năm 2032. Mình nhớ Bangkok 1999: ai mua trước khi tàu chạy là thắng lớn nhất." (carousel/video, kết nối slide Bangkok)
2. "4 tháng đầu 2026 Đà Nẵng 6 triệu lượt khách. Tăng 19%. Hạ tầng và du lịch đang chạy nhanh hơn thị trường BĐS phản ứng." (ảnh cá nhân, góc nhìn thị trường)
3. "Khi nhà ga đường sắt được chốt vị trí, BĐS xung quanh sẽ phản ứng. Đó là lúc mua đắt nhất. Câu hỏi là mua trước hay sau?" (video market)

### Thu Hút Đầu Tư Đà Nẵng 2026 — DDI Gấp 3, FDI Gấp 2,6 Lần

**Nguồn:** Báo Đà Nẵng + BNews + Thời báo TCVN | **Tên nguồn:** Báo Đà Nẵng | **Thêm:** 2026-06-12 | **Status:** PENDING
**Tags:** #thị-trường #vĩ-mô #video #carousel

**Tóm tắt:**
5 tháng đầu 2026, tổng vốn đầu tư trong nước vào Đà Nẵng đạt 71.050 tỷ, gấp 2-3 lần cùng kỳ 2025, 42 dự án mới với 63.190 tỷ (vốn gấp 4 lần). FDI đạt 313 triệu USD, tăng 2,6 lần. Mục tiêu GRDP tăng trên 11% năm 2026. Dòng vốn tập trung thương mại, dịch vụ, đô thị, hạ tầng.

**Data/Quotes:**

- DDI 5T đầu 2026: 71.050 tỷ, gấp 2-3 lần cùng kỳ (nguồn: Báo Đà Nẵng/BNews)
- FDI 5T: 313 triệu USD, tăng 2,6 lần; 57 dự án mới (nguồn: Thời báo TCVN)
- Mục tiêu GRDP 2026: tăng trên 11%
- Góp vốn mua cổ phần tăng gần 5 lần so cùng kỳ

**Hook ideas:**

1. "Đà Nẵng 5 tháng đầu 2026: vốn đầu tư trong nước gấp 3, FDI gấp 2,6 lần cùng kỳ. Khi tiền đổ vào thành phố nhanh hơn trước, BĐS thường đi đâu tiếp theo?" (carousel)
2. "Mình hay dùng 1 câu: dòng tiền đi trước, giá đi sau. Đây là lý do mình nhìn số FDI và DDI trước khi tư vấn khách." (ảnh cá nhân)

### Thị Trường BĐS Đà Nẵng 2026 — Giá Đất, Dòng Vốn, Nhà Đầu Tư Đứng Xướng Tiền

**Nguồn:** VnExpress (3 bài) | **Tên nguồn:** VnExpress | **Thêm:** 2026-06-12 | **Status:** PENDING
**Tags:** #thị-trường #giá-đất #video #carousel #ảnh

**Tóm tắt:**
Đà Nẵng 2026: giá đất trung tâm (Hải Châu, Thanh Khê) đi ngang do quỹ đất hạn chế và thanh khoản thấp, ven biển tăng nhanh hơn nhờ du lịch phục hồi. Dòng vốn quốc tế vào qua 3 kênh: FDI dự án khách sạn/resort, M&A tài sản khó khăn, vốn cá nhân Việt kiều/người nước ngoài. Nhiều nhà đầu tư đứng xướng tiền vì áp lực lãi vay — phần lớn dùng vốn tự có, không còn đòn bẩy mạnh như trước.

**Data/Quotes:**

- Giá ven sông Hàn: 3.500-7.000 USD/m², tăng 10-12%/năm (nguồn: CBRE, trích VnExpress)
- 2T đầu 2026: 1.600 căn hộ được tiêu thụ, gấp 10,4 lần cùng kỳ (nguồn: VnExpress/CafeF)
- Giá sơ cấp tăng 5-10% so cuối 2025, không giảm sâu
- Ven biển hưởng lợi từ du lịch phục hồi: condotel, second home, shophouse du lịch là phân khúc tăng nhanh hơn nội đô

**Hook ideas:**

1. "Nhiều người hỏi mình: bây giờ có nên chờ giá giảm không? Mình thấy 2 tháng đầu 2026 có 1.600 căn hộ được mua, gấp 10 lần cùng kỳ. Ai đang chờ đang chờ ai?" (ảnh cá nhân, hook câu hỏi)
2. "Giá ven sông Hàn tăng 10-12%/năm theo CBRE. Người đứng ngoài chờ giảm — người bên trong đang tích lũy." (carousel)
3. "Nhà đầu tư đứng xướng tiền vì áp lực giá và lãi vay. Mình thấy điều này mỗi ngày. Không phải vì thị trường xấu — vì họ dùng đòn bẩy sai cách." (ảnh cá nhân, góc nhìn nghề)

### Căn Hộ Ven Sông Hàn < 5 Tỷ — Dữ Liệu Cho Thuê + Lời Khuyên Tư Vấn

**Nguồn:** VnExpress (2 bài) + Dân Trí + CafeF | **Tên nguồn:** VnExpress + Dân Trí | **Thêm:** 2026-06-12 | **Status:** PENDING
**Tags:** #thị-trường #tư-vấn #căn-hộ #ảnh #carousel

**Tóm tắt:**
Ven sông Hàn là "trục dòng tiền" với giá thuê 18-40 triệu/tháng (Sun Cosmo/Panoma). Studio và 1PN là loại căn được săn nhiều nhất 2026 vì dễ lấp đầy và thu hồi vốn nhanh. Q1/2026 ĐN đón 4,2 triệu lượt khách lưu trú, tăng 15,3%. Với 3 tỷ vốn tự có, mua giai đoạn 2026 hợp lý hơn chờ giá giảm sâu vì giá đang tăng nhẹ 5-10%. Vay thêm 1,5-2 tỷ, ưu tiên studio/1PN ven sông.

**Data/Quotes:**

- Giá thuê ven sông Hàn (Sun Cosmo/Panoma): 18-40 triệu/tháng tùy căn và view (nguồn: Dân Trí)
- Quý I 2026: 4,2 triệu lượt khách lưu trú ĐN, tăng 15,3% (nguồn: Dân Trí)
- 2T đầu 2026: 1.600 căn giao dịch, gấp 10,4 lần cùng kỳ — giá tăng 5-10% (nguồn: CafeF)
- Studio/1PN là loại căn "nóng nhất" thị trường cho thuê ĐN 2026

**Hook ideas:**

1. "Khách hỏi mình: có 3 tỷ, nên vay mua căn hộ hay chờ giá giảm? Mình hỏi lại: đợi bao lâu, trong khi 2 tháng đầu năm giá đã tăng 5-10%?" (ảnh cá nhân, pain point khách)
2. "Studio ven sông Hàn cho thuê 18-40 triệu/tháng. Đây không phải con số lý tưởng. Đây là số thực đang chạy ở các dự án Sun Group." (carousel, có cite nguồn)
3. "Dưới 5 tỷ mua căn hộ Đà Nẵng: mình hay khuyên chọn studio/1PN ven sông hơn căn 2PN nội đô xa trung tâm. Lý do là tỷ lệ lấp đầy khác nhau rõ rệt." (video market/ảnh cá nhân)

### Khu TMTD Đà Nẵng — 3 Doanh Nghiệp Lớn Rót 15.025 Tỷ, 910 Ha

**Nguồn:** VnExpress + Tuổi Trẻ + Báo Đầu Tư | **Tên nguồn:** VnExpress + Tuổi Trẻ | **Thêm:** 2026-06-12 | **Status:** PENDING
**Tags:** #thị-trường #hạ-tầng #khu-TMTD #video #carousel

**Tóm tắt:**
Đến 11/6/2026, FTZ Đà Nẵng có 3 dự án hạ tầng khu chức năng với tổng vốn 15.025 tỷ: (1) Sài Gòn-Đà Nẵng, 75ha, 1.568 tỷ; (2) Phương Trang tại phường Hải Vân, 500ha, 8.119 tỷ; (3) Thanh Bình Phú Mỹ tại xã Ba Nà (KCN FTZ Phú Mỹ 3), 335ha, 5.338 tỷ. Tổng 910ha. FTZ đang chuyển từ giai đoạn cơ chế/quy hoạch sang triển khai thực tế. Không phải BĐS nhà ở để bán lẻ.

**Data/Quotes:**

- 3 dự án hạ tầng FTZ, tổng 910ha, 15.025 tỷ đồng (nguồn: VnExpress + Tuổi Trẻ + Báo Đầu Tư)
- Phương Trang: 500ha tại phường Hải Vân, 8.119 tỷ — lớn nhất
- Thanh Bình Phú Mỹ: KCN FTZ Phú Mỹ 3 tại xã Ba Nà, 335ha
- Đây là hạ tầng logistics/KCN, không phải sản phẩm nhà ở. Nhưng kéo theo nhu cầu nhà ở công nhân, chuyên gia, dịch vụ xung quanh

**Hook ideas:**

1. "910 ha logistics và KCN vừa được bật đèn xanh tại Đà Nẵng. 3 ông lớn rót 15.025 tỷ. Không phải BĐS nhà ở. Nhưng khu vực Hải Vân và Ba Nà từ đây sẽ khác." (carousel/video)
2. "FTZ Đà Nẵng từ quy hoạch sang triển khai thực tế. Đây là điểm khác biệt: trước là kế hoạch, giờ là tiền thật đổ vào đất thật." (ảnh cá nhân, góc nhìn thị trường)

## Dự Án

_Entries về Symphony 5, FourS Tower, các dự án cạnh tranh_

---

## Nghề

_Entries về kỹ năng môi giới, bán hàng, tư vấn, cộng đồng sales_

---

## Cá Nhân / Cộng Đồng

_Entries về AI, công cụ, lifestyle, truyền cảm hứng_
