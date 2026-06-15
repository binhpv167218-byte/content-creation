"""
Chuyển clip ngang → 9:16 dọc
Background: blur clip gốc scale lên full 1080x1920
Foreground: clip gốc giữ nguyên tỉ lệ, canh giữa
"""

import sys
import subprocess
import imageio_ffmpeg

INPUT  = sys.argv[1] if len(sys.argv) > 1 else "studio/raw/24_5-5.MOV"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "studio/test_vertical.mp4"

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

cmd = [
    ffmpeg, "-y",
    "-noautorotate",
    "-i", INPUT,
    "-filter_complex",
    "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
    "crop=1080:1920,boxblur=25:5[bg];"
    "[0:v]scale=w=1080:h=1920:force_original_aspect_ratio=decrease,setsar=1[fg];"
    "[bg][fg]overlay=(W-w)/2:(H-h)/2",
    "-an",
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "23",
    "-map_metadata", "-1",
    "-movflags", "+faststart",
    OUTPUT
]

print(f"Input:  {INPUT}")
print(f"Output: {OUTPUT}")
print("Đang xử lý...")

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    print("Done!")
else:
    print("Lỗi:")
    print(result.stderr[-2000:])
