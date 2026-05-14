#!/usr/bin/env python3
"""
Research bot — truy vấn thời gian thực qua Perplexity API (sonar-pro).

Dùng trực tiếp:
    python3 scripts/research_bot.py "Sun Symphony Residence 5 giá bán 2026"
    python3 scripts/research_bot.py "FourS Tower" --output context/projects/fours-tower.md

Dùng từ code:
    from scripts.research_bot import research
"""

import argparse
import os
import sys
from datetime import datetime

import requests

API_URL = "https://api.perplexity.ai/chat/completions"
MODEL   = "sonar-pro"

SYSTEM_PROMPT = """Bạn là trợ lý nghiên cứu bất động sản chuyên về thị trường Đà Nẵng, Việt Nam.

Khi được hỏi về một dự án BĐS, hãy trả lời đầy đủ theo các mục sau (bỏ qua mục nào không có thông tin):

## Tổng Quan Dự Án
- Tên, chủ đầu tư, vị trí cụ thể, quy mô (diện tích, số căn/lô), loại hình sản phẩm

## Vị Trí & Kết Nối
- Tọa độ/địa chỉ, khoảng cách đến các tiện ích trọng điểm (sân bay, biển, trung tâm)

## Giai Đoạn Hiện Tại
- Dự án đang ở giai đoạn nào (quy hoạch / xây dựng / mở bán / bàn giao)
- Phân khu nào đã mở, phân khu nào sắp mở

## Tình Trạng Pháp Lý
- Loại sổ (sở hữu lâu dài / 50 năm), giấy phép xây dựng, đủ điều kiện mở bán chưa

## Tiến Độ Xây Dựng
- Tiến độ hiện tại, mốc bàn giao, hạng mục đã/chưa hoàn thành

## Ngày Mở Bán & Booking
- Ngày nhận booking, ngày mở bán chính thức, đợt mở bán tiếp theo (nếu có)

## Giá Bán Chính Thức (Sơ Cấp)
- Bảng giá từ chủ đầu tư hoặc đại lý F1, kèm loại sản phẩm, diện tích, giá/m²
- Nếu dự án đã mở bán: giá hiện tại đang chào bán là bao nhiêu (cập nhật nhất có thể)
- Phân biệt rõ: giá gốc CĐT / giá sau chiết khấu / giá đã VAT

## Giá Thị Trường & Thứ Cấp
- **Nếu dự án đã mở bán hoặc đã bàn giao**: bắt buộc tìm giá sang nhượng/thứ cấp hiện tại trên các sàn (batdongsan.com, nha.vn, homedy...), kèm mức chênh lệch so với giá gốc CĐT
- Giá rumor đang lan truyền trong cộng đồng môi giới (ghi rõ nguồn là rumor)
- Xu hướng giá: đang tăng / giữ nguyên / giảm so với đợt mở bán trước

## Chính Sách Bán Hàng
- Phương thức thanh toán, % vốn tự có, lãi suất ưu đãi, thời gian ân hạn, chiết khấu

## Thông Tin Khác Đáng Chú Ý
- Tin tức mới nhất, thay đổi pháp lý, rủi ro, điểm mạnh nổi bật

---
Quy tắc bắt buộc khi trả lời:
- Trả về Markdown sạch, có cấu trúc rõ ràng — dùng bảng cho dữ liệu giá
- CHỈ bao gồm thông tin thực tế, có thể xác minh, có nguồn gốc rõ ràng
- Ưu tiên số liệu cụ thể (giá/m², tỷ suất, tiến độ, pháp lý) hơn mô tả chung chung
- Ghi rõ ngày/tháng/năm của thông tin nếu biết
- Nếu thông tin mâu thuẫn giữa các nguồn, ghi chú cả hai phía
- KHÔNG viết lời mở đầu, KHÔNG tóm tắt cuối bài, KHÔNG có câu "Dưới đây là..."
- Tối đa 900 từ. Ngắn gọn, dense thông tin."""


# ─────────────────────────────────────────────
# CORE
# ─────────────────────────────────────────────

def _read_api_key() -> str:
    key = os.environ.get("PERPLEXITY_API_KEY", "")
    if key:
        return key
    env_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("PERPLEXITY_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if key:
                        return key
    return ""


def _call_perplexity(system: str, user: str, recency: str = "month",
                     max_tokens: int = 1024) -> dict:
    api_key = _read_api_key()
    if not api_key:
        sys.exit("ERROR: PERPLEXITY_API_KEY không tìm thấy trong .env")

    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "search_recency_filter": recency,
            "return_citations": True,
            "max_tokens": max_tokens,
            "temperature": 0.1,
        },
        timeout=60,
    )
    if resp.status_code != 200:
        sys.exit(f"ERROR {resp.status_code}: {resp.text}")
    return resp.json()


# ─────────────────────────────────────────────
# RESEARCH
# ─────────────────────────────────────────────

def research(query: str, recency: str = "month") -> str:
    """Truy vấn Perplexity và trả về Markdown."""
    data    = _call_perplexity(SYSTEM_PROMPT, query, recency=recency, max_tokens=1024)
    content = data["choices"][0]["message"]["content"].strip()

    citations = data.get("citations", [])
    if citations:
        content += "\n\n## Nguồn\n"
        for i, url in enumerate(citations, 1):
            content += f"{i}. {url}\n"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"_Cập nhật: {ts} — Model: {MODEL}_\n\n" + content


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Research bot via Perplexity sonar-pro")
    p.add_argument("query", help="Câu truy vấn hoặc tên dự án")
    p.add_argument("--output", default=None,
                   help="Lưu kết quả research vào file .md")
    p.add_argument("--recency", default="month",
                   choices=["day", "week", "month", "year"])
    args = p.parse_args()

    result = research(args.query, recency=args.recency)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Saved: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
