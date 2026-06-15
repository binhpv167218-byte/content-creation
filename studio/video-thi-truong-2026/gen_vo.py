#!/usr/bin/env python3
import requests, time, os

KEY = os.environ.get("MINIMAX_API_KEY", "sk-api-JHaf0opo08X2DM5EQQB-kjL7iuJOlp9qv2Veg8ZXBuNd4UzmyUMlyvHh7AfR7TL0sQ5j7egYLo3LssEftiaFyOxNApuh0uLUee_n2C8FdmfU3j5M69eKaQM")
VOICE = "moss_audio_f86a4aa6-6304-11f1-ae71-da201e9a1a2f"

segs = [
    ("vo_s0", "Câu mình hay nhận nhất từ đầu năm đến giờ: Đà Nẵng hai không hai sáu nên mua chưa? Câu trả lời không phải có hay không."),
    ("vo_s1", "Giá đã thoát đáy so với giai đoạn hai không hai ba đến hai không hai bốn. Căn hộ ven biển Mỹ Khê từ bốn mươi đến năm mươi lăm triệu mỗi mét vuông. Khu mới Ngũ Hành Sơn, Hòa Xuân từ hai mươi lăm đến ba mươi lăm triệu."),
    ("vo_s2", "Mua ở thực: thị trường đang có hàng. Sản phẩm dưới ba tỷ, pháp lý rõ, khu dân cư ổn định. Đây là thời điểm ổn để vào nếu bạn mua để ở thật sự."),
    ("vo_s3", "Mua để cho thuê dài hạn: tỷ suất đang hấp dẫn. Căn hộ một đến hai phòng ngủ gần biển cho thuê từ bảy đến chín phần trăm. Du lịch tăng gần hai mươi mốt phần trăm là nền tảng tốt cho cho thuê."),
    ("vo_s4", "Lướt sóng ngắn? Thanh khoản thứ cấp vẫn thấp, thời gian thoát hàng chưa nhanh. Nếu bạn cần tiền trong mười hai đến mười tám tháng, thị trường này chưa phù hợp lúc này."),
    ("vo_s5", "Nhà đầu tư từ Hà Nội và Sài Gòn đang quay lại. Khách thuê chuyên gia nước ngoài tăng theo đà du lịch. Đây là tín hiệu cho trung và dài hạn, không phải cho lướt sóng."),
    ("vo_s6", "Câu hỏi nên mua chưa phụ thuộc vào mục đích của bạn. Ở thực, cho thuê dài hạn, tích lũy, hay cần tiền nhanh. Mỗi mục đích dẫn đến một quyết định khác nhau."),
    ("vo_s7", "Theo dõi Bình để cập nhật thị trường Đà Nẵng mỗi tuần."),
]

os.makedirs("assets", exist_ok=True)
for name, text in segs:
    path = f"assets/{name}.mp3"
    r = requests.post("https://api.minimaxi.chat/v1/t2a_v2",
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        json={"model": "speech-02-hd", "text": text, "stream": False,
              "voice_setting": {"voice_id": VOICE, "speed": 1.22, "vol": 1.0, "pitch": 0},
              "audio_setting": {"sample_rate": 44100, "bitrate": 128000, "format": "mp3"}})
    d = r.json()
    if "data" in d:
        audio = bytes.fromhex(d["data"]["audio"])
        open(path, "wb").write(audio)
        print(f"OK {name} {len(audio)//1024}KB")
    else:
        print(f"ERR {name}", d)
    time.sleep(0.5)
print("DONE")
