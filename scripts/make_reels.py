"""
make_reels.py — Ghép 9 clips thành Reels 60s, nhịp cắt theo beat nhạc
Dùng ffmpeg trực tiếp, không moviepy.
"""

import subprocess, os, shutil, librosa, imageio_ffmpeg

FFMPEG     = imageio_ffmpeg.get_ffmpeg_exe()
VIDEO_DIR  = "studio/raw"
TEMP_DIR   = "studio/temp_clips"
MUSIC_FILE = "studio/music2.mp3"
OUTPUT     = "studio/reels_final.mp4"
TRIM_START = 2.0   # bỏ N giây đầu mỗi clip (tay run)

# timelapse: True = tăng tốc (đi xe)
# speed: hệ số tăng tốc (chỉ dùng khi timelapse=True)
# seek: bắt đầu lấy từ giây bao nhiêu trong clip gốc
# target: số giây mong muốn trong output
CLIPS_CONFIG = [
    {"file": "24_5-2.MOV",  "timelapse": True,  "speed": 8,  "seek": 10, "target": 6},
    {"file": "24_5-3.MOV",  "timelapse": True,  "speed": 8,  "seek": 5,  "target": 6},
    {"file": "24_5-4.MOV",  "timelapse": True,  "speed": 6,  "seek": 5,  "target": 6},
    {"file": "24_5-5.MOV",  "timelapse": False, "speed": 1,  "seek": 5,  "target": 7},
    {"file": "24_5-6.MOV",  "timelapse": False, "speed": 1,  "seek": 10, "target": 7},
    {"file": "24_5-7.MOV",  "timelapse": False, "speed": 1,  "seek": 8,  "target": 7},
    {"file": "24_5-8.MOV",  "timelapse": False, "speed": 1,  "seek": 5,  "target": 7},
    {"file": "24_5-9.MOV",  "timelapse": False, "speed": 1,  "seek": 8,  "target": 7},
    {"file": "24_5-10.MOV", "timelapse": False, "speed": 1,  "seek": 3,  "target": 7},
]


def beat_aligned_durations(music_path, targets):
    print("Phân tích beat nhạc...")
    total = sum(targets) + 5
    y, sr = librosa.load(music_path, duration=total)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beats = librosa.frames_to_time(beat_frames, sr=sr).tolist()
    print(f"BPM: {float(tempo):.1f}")

    durations = []
    cursor = 0.0
    for t in targets:
        target_end = cursor + t
        nearest = min(beats, key=lambda b: abs(b - target_end))
        dur = max(nearest - cursor, 2.0)
        durations.append(dur)
        cursor += dur
    return durations


def process_clip(cfg, out_duration, out_path):
    speed     = cfg["speed"] if cfg["timelapse"] else 1
    seek      = cfg["seek"]
    src_dur   = out_duration * speed  # bao nhiêu giây cần lấy từ nguồn

    # Dùng trim trong filter để tránh HEVC seek corrupt frames
    trim_end  = seek + src_dur
    if cfg["timelapse"]:
        # trim → reset pts → speed up → split
        pre = f"trim=start={seek}:end={trim_end},setpts=(PTS-STARTPTS)/{speed}"
    else:
        pre = f"trim=start={seek}:end={trim_end},setpts=PTS-STARTPTS"

    filter_complex = (
        f"[0:v]{pre},split[v1][v2];"
        f"[v1]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,boxblur=25:5[bg];"
        f"[v2]scale=w=1080:h=1920:force_original_aspect_ratio=decrease,"
        f"setsar=1[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2[out]"
    )

    cmd = [
        FFMPEG, "-y",
        "-i", f"{VIDEO_DIR}/{cfg['file']}",
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-an",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-map_metadata", "-1",
        "-movflags", "+faststart",
        out_path
    ]

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR:\n{r.stderr[-800:]}")
        return False
    return True


def main():
    os.makedirs(TEMP_DIR, exist_ok=True)

    targets   = [c["target"] for c in CLIPS_CONFIG]
    durations = beat_aligned_durations(MUSIC_FILE, targets)
    total_dur = sum(durations)
    print(f"Tổng: {total_dur:.1f}s | {len(CLIPS_CONFIG)} clips\n")

    temp_files = []
    for i, (cfg, dur) in enumerate(zip(CLIPS_CONFIG, durations)):
        out   = f"{TEMP_DIR}/clip_{i:02d}.mp4"
        label = "timelapse" if cfg["timelapse"] else "normal"
        print(f"[{i+1}/{len(CLIPS_CONFIG)}] {cfg['file']} ({label}) → {dur:.2f}s")
        if process_clip(cfg, dur, out):
            temp_files.append(out)
            print("  ✓")
        else:
            print("  ✗ SKIP")

    if not temp_files:
        print("Không có clip nào!")
        return

    # Concat list
    concat_txt = f"{TEMP_DIR}/concat.txt"
    with open(concat_txt, "w") as f:
        for tf in temp_files:
            f.write(f"file '{os.path.abspath(tf)}'\n")

    # Ghép — re-encode để tránh lỗi PTS khi nối
    concat_out = f"{TEMP_DIR}/joined.mp4"
    print("\nGhép clips...")
    subprocess.run([
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_txt,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        concat_out
    ], capture_output=True)

    # Thêm nhạc + fade in/out
    print("Thêm nhạc...")
    fade_start = total_dur - 2
    r = subprocess.run([
        FFMPEG, "-y",
        "-i", concat_out,
        "-i", MUSIC_FILE,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-af", f"afade=t=in:st=0:d=1,afade=t=out:st={fade_start:.1f}:d=2",
        "-t", str(total_dur),
        "-shortest",
        OUTPUT
    ], capture_output=True, text=True)

    if r.returncode == 0:
        print(f"\nDone! → {OUTPUT}")
    else:
        print(f"Lỗi audio:\n{r.stderr[-500:]}")

    shutil.rmtree(TEMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
