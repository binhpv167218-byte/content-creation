#!/usr/bin/env python3
import requests, time, os

KEY = os.environ.get("MINIMAX_API_KEY", "sk-api-JHaf0opo08X2DM5EQQB-kjL7iuJOlp9qv2Veg8ZXBuNd4UzmyUMlyvHh7AfR7TL0sQ5j7egYLo3LssEftiaFyOxNApuh0uLUee_n2C8FdmfU3j5M69eKaQM")
VOICE = "moss_audio_f86a4aa6-6304-11f1-ae71-da201e9a1a2f"

segs = [
    ("vo_s0", "Khách hỏi mình: anh ơi, Symphony năm là condotel đúng không? Mình nói: không. Hoàn toàn không."),
    ("vo_s1", "Năm mươi năm thương mại dịch vụ khiến nhiều người e ngại. Họ liên tưởng đến condotel, loại hình bị siết chặt, pháp lý mập mờ. Đó là nhầm lẫn lớn nhất khi nhìn vào Symphony năm."),
    ("vo_s2", "Condotel thường không có sổ riêng từng căn. Bạn mua một phần trong khối sổ chung. Bán khó, thế chấp khó, pháp lý phụ thuộc vào chủ đầu tư quản lý."),
    ("vo_s3", "Symphony năm khác hoàn toàn. Có sổ đỏ riêng từng căn. Không phải sổ chung của tòa nhà. Chủ sở hữu toàn quyền mua bán, thế chấp, để lại thừa kế."),
    ("vo_s4", "Pháp lý năm mươi năm thương mại dịch vụ còn cho phép khai thác cho thuê ngắn ngày đúng luật. Airbnb, cho thuê theo đêm, đón khách du lịch. Điều mà căn hộ nhà ở vĩnh viễn thông thường không được làm."),
    ("vo_s5", "S một, S hai, S ba trong cùng tổ hợp là nhà ở lâu dài. S năm là thương mại dịch vụ. Cùng một chủ đầu tư, hai loại hình phục vụ hai mục đích. Biết cái nào phù hợp với mình mới quan trọng."),
    ("vo_s6", "Câu hỏi đúng không phải là năm mươi năm hay vĩnh viễn. Câu hỏi đúng là: pháp lý có sạch không, sổ có ra không, và mình dùng căn hộ để làm gì."),
    ("vo_s7", "Có câu hỏi cụ thể về pháp lý Symphony năm, nhắn Bình."),
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
