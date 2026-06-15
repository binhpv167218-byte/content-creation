#!/usr/bin/env python3
"""
Label video clips with descriptive names.
Workflow: ffmpeg extract thumbnail → Claude Haiku analyze image → generate descriptive name.
Không dùng Gemini — để dành quota cho việc khác.

Usage:
    python3 scripts/label-clips.py              # analyze tất cả, lưu catalog
    python3 scripts/label-clips.py --limit 5    # test 5 clips đầu
    python3 scripts/label-clips.py --rename     # analyze + rename files thật
    python3 scripts/label-clips.py --dir studio/_shared/footage/clips/hd30
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent

CLIP_DIRS = [
    WORKSPACE / "studio/_shared/footage/clips/hd30",
    WORKSPACE / "studio/_shared/footage/hd30",
]

THUMBNAILS_DIR = WORKSPACE / "outputs/clip-thumbnails"
CATALOG_FILE = WORKSPACE / "outputs/clips-catalog.json"

DELAY_S = 0.5  # delay giữa các API call (Haiku rất nhanh, không cần nhiều)


def load_env():
    env = {}
    env_file = WORKSPACE / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def get_duration(video_path):
    """ffprobe lấy duration (giây)."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def extract_thumbnail(video_path, output_path):
    """ffmpeg chụp frame tại giây thứ 1 (hoặc 0.5s nếu clip ngắn)."""
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-ss", "00:00:01",
            "-i", str(video_path),
            "-vframes", "1", "-q:v", "3",
            "-vf", "scale=640:-1",  # resize nhỏ để API nhanh hơn
            str(output_path),
        ],
        capture_output=True,
    )
    if not output_path.exists():
        # Clip ngắn hơn 1s — lấy frame đầu tiên
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vframes", "1", "-q:v", "3",
                "-vf", "scale=640:-1",
                str(output_path),
            ],
            capture_output=True,
        )
    return output_path.exists()


def analyze_thumbnail(api_key, image_path, original_name, duration):
    """Gọi Claude Haiku để phân tích thumbnail, trả về dict thông tin."""
    import urllib.request
    import urllib.error

    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    prompt = f"""Phân tích thumbnail này từ clip video "{original_name}" (dài {duration:.0f}s).

Trả về JSON (chỉ JSON thuần, không markdown, không giải thích):
{{
  "chu_de": "chủ thể chính, 2-4 từ không dấu, hyphen-separated. Ví dụ: phong-khach, cau-rong, beach-resort, ho-boi",
  "mau_chinh": "màu chủ đạo, 1-2 từ không dấu. Ví dụ: trang, xanh-duong, vang-am, toi",
  "goc_quay": "can-canh hoặc trung-canh hoặc toan-canh",
  "boi_canh": "noi-that hoặc ngoai-troi; them ban-ngay hoặc ban-dem nếu rõ ràng. Ví dụ: noi-that, ngoai-troi-ban-dem",
  "mo_ta_ngan": "mô tả 1 dòng tiếng Việt (có dấu) cho catalog"
}}"""

    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 256,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())

    text = result["content"][0]["text"].strip()
    # Bỏ markdown code block nếu model trả về
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    return json.loads(text)


def build_new_name(info, duration, used_names):
    """Tạo tên file mới từ thông tin phân tích."""
    dur_s = f"{round(duration)}s"
    slug = f"{info['chu_de']}_{info['mau_chinh']}_{info['goc_quay']}_{info['boi_canh']}_{dur_s}"
    # Làm sạch ký tự không hợp lệ
    slug = slug.lower().replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c in "-_")

    # Tránh trùng tên
    candidate = slug
    i = 2
    while candidate in used_names:
        candidate = f"{slug}-{i}"
        i += 1
    used_names.add(candidate)
    return candidate + ".mp4"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", help="Chỉ quét 1 thư mục cụ thể")
    parser.add_argument("--limit", type=int, default=0, help="Giới hạn số clip (để test)")
    parser.add_argument("--rename", action="store_true", help="Thực sự rename files")
    args = parser.parse_args()

    env = load_env()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY không có trong .env")
        sys.exit(1)

    # Thu thập clips
    dirs = [Path(args.dir)] if args.dir else CLIP_DIRS
    clips = []
    for d in dirs:
        if d.exists():
            clips.extend(sorted(d.glob("*.mp4")))
        else:
            print(f"WARNING: Không tìm thấy thư mục {d}")

    if args.limit:
        clips = clips[: args.limit]

    print(f"Tổng: {len(clips)} clips cần xử lý\n")

    # Load catalog cũ (để resume nếu bị ngắt)
    catalog = {}
    if CATALOG_FILE.exists():
        catalog = json.loads(CATALOG_FILE.read_text())
        print(f"Loaded catalog cũ: {len(catalog)} entries\n")

    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

    # Track tên đã dùng để tránh trùng
    used_names = {info["new_name"].replace(".mp4", "") for info in catalog.values()}

    errors = []

    for i, clip_path in enumerate(clips, 1):
        filename = clip_path.name

        if filename in catalog:
            print(f"[{i}/{len(clips)}] SKIP (cached): {filename}")
            continue

        print(f"[{i}/{len(clips)}] {filename}", end=" → ", flush=True)

        # Duration
        duration = get_duration(clip_path)

        # Thumbnail
        thumb_path = THUMBNAILS_DIR / (clip_path.stem + ".jpg")
        if not extract_thumbnail(clip_path, thumb_path):
            print("ERROR: không extract được thumbnail")
            errors.append(filename)
            continue

        # Analyze
        try:
            info = analyze_thumbnail(api_key, thumb_path, filename, duration)
            new_name = build_new_name(info, duration, used_names)

            catalog[filename] = {
                "new_name": new_name,
                "duration_s": round(duration, 1),
                "original_path": str(clip_path),
                "thumbnail": str(thumb_path),
                **info,
            }

            print(new_name)

            # Lưu sau mỗi clip — an toàn khi bị ngắt
            CATALOG_FILE.write_text(
                json.dumps(catalog, ensure_ascii=False, indent=2)
            )

        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(filename)

        if i < len(clips):
            time.sleep(DELAY_S)

    # Summary
    print(f"\nHoàn thành: {len(catalog)} clips trong catalog")
    print(f"Catalog: {CATALOG_FILE}")
    print(f"Thumbnails: {THUMBNAILS_DIR}/")

    if errors:
        print(f"\nLỗi ({len(errors)} clips): {', '.join(errors)}")

    # Rename
    if args.rename:
        print("\nRenaming...")
        renamed = 0
        for orig_name, info in catalog.items():
            orig_path = Path(info["original_path"])
            new_path = orig_path.parent / info["new_name"]
            if orig_path.exists() and not new_path.exists():
                orig_path.rename(new_path)
                print(f"  {orig_name} → {info['new_name']}")
                renamed += 1
        print(f"Renamed {renamed} files.")
    else:
        print("\nChưa rename. Preview 10 clips đầu:")
        for orig, info in list(catalog.items())[:10]:
            print(f"  {orig}")
            print(f"    → {info['new_name']} | {info.get('mo_ta_ngan', '')}")
        print("\nDùng --rename để thực sự đổi tên files.")


if __name__ == "__main__":
    main()
