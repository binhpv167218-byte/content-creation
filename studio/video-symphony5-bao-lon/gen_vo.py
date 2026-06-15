#!/usr/bin/env python3
import requests, time, os

KEY = os.environ.get("MINIMAX_API_KEY", "sk-api-JHaf0opo08X2DM5EQQB-kjL7iuJOlp9qv2Veg8ZXBuNd4UzmyUMlyvHh7AfR7TL0sQ5j7egYLo3LssEftiaFyOxNApuh0uLUee_n2C8FdmfU3j5M69eKaQM")
VOICE = "moss_audio_f86a4aa6-6304-11f1-ae71-da201e9a1a2f"

segs = [
    ("vo_s0", "Symphony một, hai, ba. Bàn giao tháng Năm. Đúng hai năm sau ngày ra mắt."),
    ("vo_s1", "VietnamNet và Diễn Đàn Doanh Nghiệp cùng đưa tin tuần này. Sun Group bàn giao Symphony một, hai, ba đúng hẹn. Trước đó là Sun Panoma và Sun Ponte. Ba dự án liên tiếp, đúng hẹn cả ba. Trong bất động sản Việt Nam, chuyện này hiếm."),
    ("vo_s2", "Không chỉ bàn giao đúng hẹn. Diễn Đàn Doanh Nghiệp xác nhận thêm, sổ đỏ hoàn tất trong vòng sáu tháng sau khi nhận nhà. Pháp lý sạch, không vướng mắc. Đó mới là bảo chứng vàng thật sự."),
    ("vo_s3", "Thị trường cho thuê: sáu triệu lượt khách bốn tháng đầu năm, tăng mười chín phần trăm. Căn hộ trung tâm ven sông Hàn đang cho thuê tám đến chín phần trăm mỗi năm. Đây là số thật từ bài báo."),
    ("vo_s4", "Mình không nói Symphony tăng bao nhiêu phần trăm. Nhưng tiến độ thật, pháp lý sạch, cho thuê được. Ba thứ này cùng một lúc, tại Đà Nẵng, hiếm lắm."),
    ("vo_s5", "Symphony Năm đang có giỏ hàng chính thức. Bạn muốn nói chuyện cụ thể, nhắn Bình."),
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
