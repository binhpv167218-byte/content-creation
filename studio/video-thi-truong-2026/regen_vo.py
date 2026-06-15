#!/usr/bin/env python3
import requests, time, os

KEY = os.environ.get("MINIMAX_API_KEY", "sk-api-JHaf0opo08X2DM5EQQB-kjL7iuJOlp9qv2Veg8ZXBuNd4UzmyUMlyvHh7AfR7TL0sQ5j7egYLo3LssEftiaFyOxNApuh0uLUee_n2C8FdmfU3j5M69eKaQM")
VOICE = "moss_audio_f86a4aa6-6304-11f1-ae71-da201e9a1a2f"

segs = [
    ("vo_s1", "Giá đã thoát đáy so với giai đoạn hai không hai ba đến hai không hai bốn. Căn hộ ven biển Mỹ Khê từ một trăm đến hai trăm triệu mỗi mét vuông. Khu mới Hòa Xuân từ bốn mươi lăm đến sáu mươi triệu."),
    ("vo_s3", "Mua để cho thuê dài hạn: tỷ suất đang hấp dẫn. Căn hộ ven sông Hàn và Mỹ Khê cho thuê từ bảy đến chín phần trăm sau chi phí. Du lịch tăng gần hai mươi mốt phần trăm là nền tảng tốt cho cho thuê."),
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
