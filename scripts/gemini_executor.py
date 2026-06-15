#!/usr/bin/env python3
"""
gemini_executor.py — Cơ Bắp Thực Thi
Nhận Blueprint từ Claude, gọi Gemini 3.5 Flash, lưu output để Claude QA.

Usage:
  python3 scripts/gemini_executor.py --blueprint <file>
  python3 scripts/gemini_executor.py --blueprint <file> --output <file>
  python3 scripts/gemini_executor.py --blueprint <file> --iteration 2
  cat blueprint.md | python3 scripts/gemini_executor.py --stdin
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.5-flash"
OUTPUT_DIR = Path("outputs/gemini_executor")
MAX_ITERATIONS = 2  # Escalation rule: sau 2 lần fail → Claude can thiệp


def build_system_prompt() -> str:
    return """Bạn là Gemini 3.5 Flash — Cơ Bắp Thực Thi trong hệ sinh thái Antigravity.

Nhiệm vụ: Nhận Blueprint kỹ thuật từ Claude Code và dịch thành mã nguồn thô hoàn chỉnh.

Quy tắc bắt buộc:
1. Viết code đầy đủ, không bỏ TODO hoặc placeholder
2. Theo đúng stack/tools đã chỉ định trong Blueprint
3. Theo đúng data flow đã mô tả
4. Output tất cả file được yêu cầu, mỗi file có header rõ ràng: // FILE: <tên file>
5. Không giải thích dài dòng — chỉ code và comment ngắn khi cần thiết
6. Nếu Blueprint yêu cầu nhiều file, xuất tất cả trong một response, phân tách bằng:
   === FILE: <path/filename> ===
   <code>
   === END FILE ==="""


def run_gemini(blueprint: str, iteration: int = 1) -> dict:
    client = genai.Client(api_key=GEMINI_API_KEY)

    iteration_note = ""
    if iteration > 1:
        iteration_note = f"\n\n[ITERATION {iteration} — Lần thực thi lại theo Toa thuốc QA]"

    prompt = f"{blueprint}{iteration_note}"

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "system_instruction": build_system_prompt(),
            "temperature": 0.2,
        },
    )

    return {
        "model": GEMINI_MODEL,
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(),
        "blueprint_length": len(blueprint),
        "output": response.text,
        "usage": {
            "input_tokens": getattr(response.usage_metadata, "prompt_token_count", None),
            "output_tokens": getattr(response.usage_metadata, "candidates_token_count", None),
        },
    }


def save_output(result: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Lưu raw code output
    output_path.write_text(result["output"], encoding="utf-8")

    # Lưu metadata kèm theo
    meta_path = output_path.with_suffix(".meta.json")
    meta = {k: v for k, v in result.items() if k != "output"}
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OUTPUT] {output_path}")
    print(f"[META]   {meta_path}")
    print(f"[TOKENS] input={result['usage']['input_tokens']} output={result['usage']['output_tokens']}")
    print(f"[ITER]   Iteration {result['iteration']}/{MAX_ITERATIONS} (escalation nếu vượt {MAX_ITERATIONS})")


def check_escalation(output_path: Path) -> None:
    meta_path = output_path.with_suffix(".meta.json")
    if not meta_path.exists():
        return
    meta = json.loads(meta_path.read_text())
    if meta.get("iteration", 1) >= MAX_ITERATIONS:
        print(f"\n[ESCALATION WARNING] Đã đến iteration {meta['iteration']}.")
        print("[ESCALATION WARNING] Theo quy tắc: Claude phải can thiệp trực tiếp lần này.")


def main():
    parser = argparse.ArgumentParser(description="Gemini Executor — Cơ Bắp Thực Thi")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--blueprint", type=str, help="Đường dẫn file Blueprint (.md hoặc .txt)")
    group.add_argument("--stdin", action="store_true", help="Đọc Blueprint từ stdin")

    parser.add_argument("--output", type=str, help="Đường dẫn lưu output (mặc định: outputs/gemini_executor/YYYYMMDD_HHMMSS.txt)")
    parser.add_argument("--iteration", type=int, default=1, help="Số lần thực thi (1=lần đầu, 2=đã fail QA 1 lần)")
    args = parser.parse_args()

    # Đọc blueprint
    if args.stdin:
        print("[INPUT] Đọc Blueprint từ stdin...")
        blueprint = sys.stdin.read().strip()
    else:
        bp_path = Path(args.blueprint)
        if not bp_path.exists():
            print(f"[ERROR] Không tìm thấy file: {bp_path}")
            sys.exit(1)
        blueprint = bp_path.read_text(encoding="utf-8").strip()

    if not blueprint:
        print("[ERROR] Blueprint rỗng.")
        sys.exit(1)

    # Xác định output path
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"output_{timestamp}_iter{args.iteration}.txt"

    print(f"[MODEL]  {GEMINI_MODEL}")
    print(f"[ITER]   {args.iteration}/{MAX_ITERATIONS}")
    print(f"[INPUT]  {len(blueprint)} ký tự")
    print("Đang gọi Gemini...")

    result = run_gemini(blueprint, iteration=args.iteration)
    save_output(result, output_path)
    check_escalation(output_path)

    print("\n[DONE] Claude đọc output tại:", output_path)


if __name__ == "__main__":
    main()
