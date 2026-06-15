import { analyzeVideo } from "./analyze-video.js";

const result = await analyzeVideo(
  "studio/_shared/footage/canh-danang-4k-01.mp4",
  "Mô tả chi tiết nội dung video này: có gì trong video, cảnh quay ở đâu, màu sắc, không khí, phù hợp dùng cho loại nội dung nào?",
);

console.log(result);
