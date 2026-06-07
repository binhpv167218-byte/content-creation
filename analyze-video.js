import { GoogleGenerativeAI } from "@google/generative-ai";
import { GoogleAIFileManager } from "@google/generative-ai/server";
import * as path from "path";
import dotenv from "dotenv";
dotenv.config();

const API_KEY = process.env.GEMINI_API_KEY;
const genAI = new GoogleGenerativeAI(API_KEY);
const fileManager = new GoogleAIFileManager(API_KEY);

// Phân tích video sâu (YouTube URL + local file) — cần 2.5-flash, 3.5 chưa hỗ trợ video input
const videoModel = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

// Việc lặt vặt: đặt tên file, extract metadata, classify — 1500 RPD free
const liteModel = genAI.getGenerativeModel({ model: "gemini-3.5-flash" });

function isYouTubeUrl(input) {
  return /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)/.test(input);
}

// Strip &t=... timestamp param — Gemini không nhận URL có timestamp
function cleanYouTubeUrl(url) {
  const u = new URL(url);
  u.searchParams.delete("t");
  return u.toString();
}

// Phân tích video từ YouTube URL hoặc file local MP4
async function analyzeVideo(videoPathOrUrl, task) {
  if (isYouTubeUrl(videoPathOrUrl)) {
    const cleanUrl = cleanYouTubeUrl(videoPathOrUrl);
    console.log("Analyzing YouTube video...");
    videoPathOrUrl = cleanUrl;
    const result = await videoModel.generateContent({
      contents: [
        {
          parts: [{ text: task }, { fileData: { fileUri: videoPathOrUrl } }],
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

// Phân tích video dùng lite model — tiết kiệm quota (1500 RPD free)
async function analyzeVideoLite(videoPathOrUrl, task) {
  const absolutePath = path.resolve(videoPathOrUrl);
  const fileName = path.basename(absolutePath);

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

  const result = await liteModel.generateContent({
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

export { analyzeVideo, analyzeVideoLite, quickTask };
