import { analyzeVideo } from "./analyze-video.js";
import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";

const CLIP_DURATION = 4; // giây mỗi clip

async function splitAndLabel(videoPath, outputDir) {
  const absInput = path.resolve(videoPath);
  const baseName = path.basename(videoPath, ".mp4");

  fs.mkdirSync(outputDir, { recursive: true });

  // Lấy duration
  const duration = parseFloat(
    execSync(
      `ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${absInput}"`,
    )
      .toString()
      .trim(),
  );

  const totalClips = Math.floor(duration / CLIP_DURATION);
  console.log(
    `Video: ${baseName} (${duration.toFixed(1)}s) → ${totalClips} clips\n`,
  );

  for (let i = 0; i < totalClips; i++) {
    const start = i * CLIP_DURATION;
    const tempPath = path.join(outputDir, `_temp_clip_${i}.mp4`);

    // Cắt clip
    execSync(
      `ffmpeg -y -ss ${start} -t ${CLIP_DURATION} -i "${absInput}" -c copy "${tempPath}" -loglevel quiet`,
    );

    console.log(`Clip ${i + 1}/${totalClips}: phân tích...`);

    // Gemini phân tích
    const description = await analyzeVideo(
      tempPath,
      "Mô tả ngắn gọn nội dung clip này trong 5-8 từ tiếng Anh, dùng dấu gạch ngang thay khoảng trắng, chữ thường. Chỉ trả về tên file, không giải thích thêm. Ví dụ: luxury-apartment-living-room-sunlight",
    );

    const slug = description
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9-]/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-|-$/g, "");

    const finalPath = path.join(outputDir, `${slug}.mp4`);
    fs.renameSync(tempPath, finalPath);
    console.log(`  → ${slug}.mp4`);
  }

  console.log(`\nXong! Clips saved to: ${outputDir}`);
}

// Test với 1 video
await splitAndLabel(
  "studio/_shared/footage/canho-noi-that-4k-05.mp4",
  "studio/_shared/footage/clips",
);
