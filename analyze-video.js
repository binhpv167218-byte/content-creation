import { GoogleGenerativeAI } from "@google/generative-ai";
import { GoogleAIFileManager } from "@google/generative-ai/server";
import * as path from "path";
import dotenv from "dotenv";
dotenv.config();

const API_KEY = process.env.GEMINI_API_KEY;
const genAI = new GoogleGenerativeAI(API_KEY);
const fileManager = new GoogleAIFileManager(API_KEY);

// Phân tích video sâu (YouTube URL + local file) — dùng model mạnh
const videoModel = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

// Việc lặt vặt: đặt tên file, extract metadata, classify — tiết kiệm quota
const liteModel = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

function isYouTubeUrl(input) {
  return /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)/.test(input);
}

// Phân tích video từ YouTube URL hoặc file local MP4
async function analyzeVideo(videoPathOrUrl, task) {
  if (isYouTubeUrl(videoPathOrUrl)) {
    console.log("Analyzing YouTube video...");
    const result = await videoModel.generateContent({
      contents: [
        {
          parts: [
            { text: task },
            { fileData: { mimeType: "video/mp4", fileUri: videoPathOrUrl } },
          ],
        },
      ],
    });
    return result.response.text();
  }

  // File local — upload lên Google AI Files API
  const absolutePath = path.resolve(videoPathOrUrl);
  const fileName = path.basename(absolutePath);

  console.log("Uploading video...");
  const uploadResult = await fileManager.uploadFile(absolutePath, {
    mimeType: "video/mp4",
    displayName: fileName,
  });

  let file = await fileManager.getFile(uploadResult.file.name);
  while (file.state === "PROCESSING") {
    await new Promise((r) => setTimeout(r, 3000));
    file = await fileManager.getFile(uploadResult.file.name);
  }

  if (file.state === "FAILED") throw new Error("Video processing failed");
  console.log("Upload done, analyzing...");

  const result = await videoModel.generateContent({
    contents: [
      {
        parts: [
          { text: task },
          { fileData: { mimeType: "video/mp4", fileUri: file.uri } },
        ],
      },
    ],
  });

  await fileManager.deleteFile(file.name);
  return result.response.text();
}

// Việc nhẹ: đặt tên file, extract metadata, phân loại — dùng gemini-1.5-flash
async function quickTask(prompt) {
  const result = await liteModel.generateContent(prompt);
  return result.response.text();
}

export { analyzeVideo, quickTask };
