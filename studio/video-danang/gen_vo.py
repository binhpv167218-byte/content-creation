#!/usr/bin/env python3
import requests, time

KEY = "sk-api-JHaf0opo08X2DM5EQQB-kjL7iuJOlp9qv2Veg8ZXBuNd4UzmyUMlyvHh7AfR7TL0sQ5j7egYLo3LssEftiaFyOxNApuh0uLUee_n2C8FdmfU3j5M69eKaQM"
VOICE = "moss_audio_f86a4aa6-6304-11f1-ae71-da201e9a1a2f"  # voice mới (duyệt 2026-06-08)
# VOICE = "moss_audio_1feb0860-5d7d-11f1-8f84-faf87dcc54b3"  # voice cũ

segs = [
    ("vo_s0", "17.3 triệu khách. Đà Nẵng đang bùng nổ du lịch — và tỷ suất cho thuê cũng đang tăng theo."),
    ("vo_s1", "Từ bãi biển Mỹ Khê đến cầu Vàng Bà Nà, từ lễ hội pháo hoa DIFF đến thành phố về đêm — đây là lý do khách quốc tế không ngừng quay lại. Năm hai không hai lăm, 7.6 triệu khách quốc tế, tăng 25 phần trăm. Cuối tuần lấp phòng 95 đến 97 phần trăm."),
    ("vo_s2", "Kết quả thực tế: Đà Nẵng xếp hạng số 1 trong 7 thành phố về tỷ suất cho thuê — 8 đến 12 phần trăm mỗi năm. Hà Nội chỉ 2 đến 4 phần trăm. Cùng vốn đầu tư — chênh 3 đến 4 lần."),
    ("vo_s3", "Cùng 1 căn hộ 2.5 tỷ tại Đà Nẵng: Airbnb mang về 20 đến 25 triệu mỗi tháng — tức 240 đến 300 triệu mỗi năm. Cùng tài sản, khác cách vận hành, lợi nhuận lệch 2 lần."),
    ("vo_s4", "Du lịch bùng nổ, tỷ suất đứng đầu, dòng tiền tốt nhất miền Trung. Bạn đang cân nhắc Đà Nẵng? Nhắn Bình — mình nói chuyện cụ thể."),
]

for name, text in segs:
    r = requests.post("https://api.minimaxi.chat/v1/t2a_v2",
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        json={"model": "speech-02-hd", "text": text, "stream": False,
              "voice_setting": {"voice_id": VOICE, "speed": 1.22, "vol": 1.0, "pitch": 0},
              "audio_setting": {"sample_rate": 44100, "bitrate": 128000, "format": "mp3"}})
    d = r.json()
    if "data" in d:
        audio = bytes.fromhex(d["data"]["audio"])
        open(f"assets/{name}.mp3", "wb").write(audio)
        print(f"OK {name} {len(audio)//1024}KB")
    else:
        print(f"ERR {name}", d)
    time.sleep(0.4)
print("DONE")
