// Cắt tất cả video nguồn thành clips 4s, đặt tên theo source + sequence.
// Không dùng AI — tên source đã mang đủ ngữ cảnh cho Claude.
// Ví dụ: canh-danang-4k-07_c03.mp4, canho-noi-that-4k-10_c05.mp4

import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";

const INPUT_DIR = "studio/_shared/footage";
const OUTPUT_DIR = "studio/_shared/footage/clips";
const CLIP_DURATION = 4; // giây
const MIN_REMAINDER = 3; // giữ phần cuối nếu >= 3s

function getDuration(filePath) {
  return parseFloat(
    execSync(
      `ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${filePath}"`,
    )
      .toString()
      .trim(),
  );
}

function cutClip(input, start, duration, output) {
  execSync(
    `ffmpeg -y -ss ${start} -t ${duration} -i "${input}" -c copy "${output}" -loglevel quiet`,
  );
}

function main() {
  // Xoá clips cũ, tạo lại thư mục sạch
  if (fs.existsSync(OUTPUT_DIR)) {
    fs.rmSync(OUTPUT_DIR, { recursive: true });
    console.log("Đã xoá clips cũ\n");
  }
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const files = fs
    .readdirSync(INPUT_DIR)
    .filter((f) => f.endsWith(".mp4"))
    .sort()
    .map((f) => path.join(INPUT_DIR, f));

  console.log(`${files.length} video nguồn\n`);

  let grandTotal = 0;

  for (const file of files) {
    const baseName = path.basename(file, ".mp4");
    const duration = getDuration(file);
    const nFull = Math.floor(duration / CLIP_DURATION);
    const remainder = duration - nFull * CLIP_DURATION;
    const nClips = nFull + (remainder >= MIN_REMAINDER ? 1 : 0);

    process.stdout.write(`── ${baseName} (${duration.toFixed(1)}s) → `);

    for (let i = 0; i < nFull; i++) {
      const clipName = `${baseName}_c${String(i + 1).padStart(2, "0")}.mp4`;
      cutClip(
        file,
        i * CLIP_DURATION,
        CLIP_DURATION,
        path.join(OUTPUT_DIR, clipName),
      );
    }

    if (remainder >= MIN_REMAINDER) {
      const clipName = `${baseName}_c${String(nFull + 1).padStart(2, "0")}.mp4`;
      cutClip(
        file,
        nFull * CLIP_DURATION,
        remainder,
        path.join(OUTPUT_DIR, clipName),
      );
    }

    console.log(`${nClips} clips`);
    grandTotal += nClips;
  }

  console.log(`\n✅ Xong! ${grandTotal} clips trong ${OUTPUT_DIR}`);
}

main();
