#!/usr/bin/env python3
import requests, time, os

KEY = os.environ.get("MINIMAX_API_KEY", "sk-api-JHaf0opo08X2DM5EQQB-kjL7iuJOlp9qv2Veg8ZXBuNd4UzmyUMlyvHh7AfR7TL0sQ5j7egYLo3LssEftiaFyOxNApuh0uLUee_n2C8FdmfU3j5M69eKaQM")
VOICE = "moss_audio_f86a4aa6-6304-11f1-ae71-da201e9a1a2f"

segs = [
    ("vo_s0", "16 tuyến metro. Đà Nẵng đang quy hoạch hơn 200 kilômét đường ray. Và bản đồ giá bất động sản sẽ thay đổi vĩnh viễn."),
    ("vo_s1", "Lịch sử đã chứng minh: bất cứ thành phố nào có metro, bất động sản trong bán kính một kilômét tăng hai mươi đến bốn mươi phần trăm sau khi khởi công. Mạng lưới Đà Nẵng: 16 tuyến, hơn 200 kilômét, phủ sóng toàn thành phố từ Liên Chiểu đến Sơn Trà."),
    ("vo_s2", "Tuyến được ưu tiên làm trước: Đà Nẵng, Hội An. Dài 31 kilômét. Vốn đầu tư bốn mươi bảy ngàn bảy trăm tỷ đồng. Khởi công đầu năm hai không hai bảy, hoàn thành năm hai không ba mươi. Từ đó, Hội An chỉ còn 20 phút."),
    ("vo_s3", "Mình đã ở thị trường này 10 năm. Mỗi lần hạ tầng lớn được công bố, người vào sớm luôn thắng. Không phải may. Là vì họ đọc được tín hiệu trước người khác."),
    ("vo_s4", "Theo dõi Bình để cập nhật khi hạ tầng tiếp theo của Đà Nẵng được công bố."),
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
