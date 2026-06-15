#!/usr/bin/env python3
import requests, time, os

KEY = os.environ.get("MINIMAX_API_KEY", "sk-api-JHaf0opo08X2DM5EQQB-kjL7iuJOlp9qv2Veg8ZXBuNd4UzmyUMlyvHh7AfR7TL0sQ5j7egYLo3LssEftiaFyOxNApuh0uLUee_n2C8FdmfU3j5M69eKaQM")
VOICE = "moss_audio_f86a4aa6-6304-11f1-ae71-da201e9a1a2f"

segs = [
    ("vo_s0", "Sun Group vừa bàn giao sổ đỏ cho cư dân Symphony một, hai, ba ngày sáu tháng sáu. Điều này quan trọng hơn bạn nghĩ."),
    ("vo_s1", "Bàn giao đúng hạn là một chuyện. Ra sổ đúng cam kết là chuyện khác. Symphony một, hai, ba làm được cả hai. Bàn giao tháng ba đến tháng năm. Sổ đỏ trao tay cư dân đầu tiên tuần đầu tháng sáu."),
    ("vo_s2", "Trong bất động sản Việt Nam, đây không phải điều hiển nhiên. Nhiều dự án bàn giao nhà nhưng sổ chờ vài năm. Người mua sống trong nhà mình mua nhưng chưa thật sự sở hữu nó. Sun Group làm khác."),
    ("vo_s3", "Mình hay dùng điều này khi tư vấn Symphony năm. Khách hỏi: chủ đầu tư có uy tín không? Mình nói: nhìn sang tòa bên cạnh. Hàng xóm đã nhận nhà, đã cầm sổ, đang khai thác."),
    ("vo_s4", "Tháng năm hai không hai sáu, Sun Group khởi công Symphony năm. Máy móc đang chạy tại công trường. Không phải lời hứa trên giấy, là công trình đang diễn ra ngay lúc này."),
    ("vo_s5", "Symphony năm là tháp cuối hoàn thiện tổ hợp tám héc ta. Khi S năm xong, toàn bộ tiện ích, hồ bơi, gym, spa, công viên năm ngàn mét vuông đều đã vận hành. Bạn vào một hệ sinh thái đã chạy, không phải chờ xây."),
    ("vo_s6", "Uy tín không tính trên lời hứa. Tính trên việc đã làm. Sun Group đã làm với S một, S hai, S ba. S năm là bước tiếp theo của cùng track record đó. Không có gì mới để chứng minh, vì đã chứng minh rồi."),
    ("vo_s7", "Bạn muốn tìm hiểu Symphony năm, Bình ở đây. Nhắn trực tiếp."),
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
        print(f"FAIL {name}: {d}")
    time.sleep(0.5)
