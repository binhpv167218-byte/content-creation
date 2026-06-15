#!/usr/bin/env python3
import requests, time, os

KEY = os.environ.get("MINIMAX_API_KEY", "sk-api-JHaf0opo08X2DM5EQQB-kjL7iuJOlp9qv2Veg8ZXBuNd4UzmyUMlyvHh7AfR7TL0sQ5j7egYLo3LssEftiaFyOxNApuh0uLUee_n2C8FdmfU3j5M69eKaQM")
VOICE = "moss_audio_f86a4aa6-6304-11f1-ae71-da201e9a1a2f"

segs = [
    ("vo_s0", "Hôm nay Sun Group bàn giao sổ đỏ cho cư dân đầu tiên Symphony một, hai, ba. Bình ở đây. Dẫn bạn vào xem."),
    ("vo_s1", "Không phải sự kiện ra mắt thông thường. Đây là lễ bàn giao sổ đỏ thật sự. Cư dân nhận giấy tờ, chụp ảnh, bắt tay."),
    ("vo_s2", "Mình để ý kỹ hơn. Khách hôm nay không chủ yếu từ Đà Nẵng. Hà Nội, Sài Gòn chiếm gần một nửa. Tín hiệu cần để ý."),
    ("vo_s3", "Phía trong có sa bàn tổ hợp Symphony. Bốn tháp: một, hai, ba và năm. Một, hai, ba vừa bàn giao. Symphony năm đang mở bán. Cùng một sự kiện, hai câu chuyện."),
    ("vo_s4", "Mình nhận ra: khách đứng ở sa bàn lâu hơn nghe thuyết trình. Người ta mua bằng hình ảnh. Không phải con số."),
    ("vo_s5", "Cái mình thích nhất ở sự kiện như vầy: cuộc trò chuyện không có trong kịch bản. Khách hay hỏi những câu mình không chuẩn bị. Đó là lúc học được nhiều nhất."),
    ("vo_s6", "Mình qua nhiều sự kiện rồi. Nhưng lễ bàn giao sổ đỏ thật sự khác. Cư dân cầm tờ giấy đó, mặt họ khác. Không phải vì giá trị tài sản. Mà vì lời hứa được giữ. Hôm nay có một khách hỏi Bình một câu về chuyện này. Video sau mình kể."),
    ("vo_s7", "Theo dõi Bình để xem thêm hậu trường như vầy nhé."),
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
