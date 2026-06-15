import { analyzeVideoLite } from "./analyze-video.js";
import * as fs from "fs";
import * as path from "path";

const CLIPS_DIR = "studio/_shared/footage/clips";
const DELAY_MS = 5000; // 5s giữa mỗi call
const MAX_RETRIES = 3;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Trích retryDelay từ error message (nếu có)
function parseRetryDelay(errMsg) {
  const m = errMsg.match(/"retryDelay":"(\d+)s"/);
  return m ? parseInt(m[1]) * 1000 + 2000 : 65000; // +2s buffer, default 65s
}

async function analyzeWithRetry(filePath, prompt) {
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      return await analyzeVideoLite(filePath, prompt);
    } catch (e) {
      const is429 = e.message.includes("429");
      const is503 = e.message.includes("503");
      if ((is429 || is503) && attempt < MAX_RETRIES) {
        const wait = is429 ? parseRetryDelay(e.message) : 30000;
        console.log(
          `\n  ⚠ ${is429 ? "429 quota" : "503 overload"} — chờ ${Math.round(wait / 1000)}s rồi retry (${attempt}/${MAX_RETRIES})...`,
        );
        await sleep(wait);
      } else {
        throw e;
      }
    }
  }
}

async function main() {
  const genericClips = fs
    .readdirSync(CLIPS_DIR)
    .filter((f) => f.startsWith("clip-") && f.endsWith(".mp4"));

  console.log(`Cần rename: ${genericClips.length} clips\n`);

  const usedNames = new Set(
    fs.readdirSync(CLIPS_DIR).map((f) => f.replace(".mp4", "")),
  );

  function uniqueSlug(slug) {
    let name = slug;
    let i = 2;
    while (usedNames.has(name)) name = `${slug}-${i++}`;
    usedNames.add(name);
    return name;
  }

  for (let i = 0; i < genericClips.length; i++) {
    const file = genericClips[i];
    const filePath = path.join(CLIPS_DIR, file);
    process.stdout.write(`[${i + 1}/${genericClips.length}] ${file} → `);

    try {
      const desc = await analyzeWithRetry(
        filePath,
        "Describe this video clip in 5-7 English words using hyphens instead of spaces, lowercase only. Return ONLY the filename slug, no explanation. Example: luxury-apartment-living-room-sunlight",
      );
      const slug = desc
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "");

      if (slug && slug.length > 5) {
        const newName = uniqueSlug(slug);
        fs.renameSync(filePath, path.join(CLIPS_DIR, `${newName}.mp4`));
        console.log(`${newName}.mp4`);
      } else {
        console.log(`(giữ nguyên — slug không hợp lệ: "${slug}")`);
      }
    } catch (e) {
      console.log(`LỖI: ${e.message.split("\n")[0]}`);
    }

    if (i < genericClips.length - 1) await sleep(DELAY_MS);
  }

  console.log("\n✅ Xong!");
}

main();
