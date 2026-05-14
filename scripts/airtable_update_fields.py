#!/usr/bin/env python3
"""
Cập nhật fields trong Airtable — đổi Ngày đăng + Ngày tạo sang dateTime.
"""

import requests
import time
from pathlib import Path


def load_env():
    env = {}
    for line in (Path(__file__).parent.parent / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


ENV     = load_env()
KEY     = ENV["AIRTABLE_API_KEY"]
BASE_ID = ENV["AIRTABLE_BASE_ID"]
HEADERS = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
META    = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}"

DATETIME_OPTIONS = {
    "dateFormat": {"name": "iso"},
    "timeFormat": {"name": "24hour"},
    "timeZone": "Asia/Ho_Chi_Minh",
}


def get_tables():
    r = requests.get(f"{META}/tables", headers=HEADERS)
    return r.json()["tables"]


def update_field(table_id, field_id, field_name):
    payload = {
        "type": "dateTime",
        "options": DATETIME_OPTIONS,
    }
    r = requests.patch(f"{META}/tables/{table_id}/fields/{field_id}", headers=HEADERS, json=payload)
    if r.status_code in (200, 201):
        print(f"  ✅ '{field_name}' → dateTime (Asia/Ho_Chi_Minh)")
    else:
        print(f"  ❌ '{field_name}': {r.text[:200]}")


def delete_field(table_id, field_id, field_name):
    r = requests.delete(f"{META}/tables/{table_id}/fields/{field_id}", headers=HEADERS)
    if r.status_code in (200, 201):
        print(f"  🗑  Đã xóa field cũ '{field_name}'")
    else:
        print(f"  ⚠️  Không xóa được '{field_name}': {r.text[:200]}")


def create_datetime_field(table_id, name, description=""):
    payload = {
        "name": name,
        "type": "dateTime",
        "options": DATETIME_OPTIONS,
    }
    if description:
        payload["description"] = description
    r = requests.post(f"{META}/tables/{table_id}/fields", headers=HEADERS, json=payload)
    if r.status_code in (200, 201):
        print(f"  ✅ Tạo field '{name}' kiểu dateTime (GMT+7)")
    else:
        print(f"  ❌ Tạo field '{name}' thất bại: {r.text[:200]}")


def main():
    tables = get_tables()
    posts_table = next((t for t in tables if "📝 Posts" in t["name"]), None)

    if not posts_table:
        print("❌ Không tìm thấy bảng 📝 Posts")
        return

    table_id = posts_table["id"]
    existing = {f["name"]: f["id"] for f in posts_table["fields"]}

    print(f"📋 Cập nhật fields ngày/giờ trong bảng '📝 Posts'...")

    # Rename field cũ (date) → tạo field mới (dateTime) cùng tên
    for name in ["Ngày đăng", "Ngày tạo"]:
        if name in existing:
            # Rename field cũ sang tên tạm
            r = requests.patch(
                f"{META}/tables/{table_id}/fields/{existing[name]}",
                headers=HEADERS,
                json={"name": f"_{name}_old"},
            )
            if r.status_code in (200, 201):
                print(f"  ↩  Đổi tên '{name}' → '_{name}_old'")
            else:
                print(f"  ⚠️  Không rename được '{name}': {r.text[:150]}")
                continue
            time.sleep(0.3)
        create_datetime_field(table_id, name)
        time.sleep(0.3)

    print("\nXong. Refresh Airtable để thấy thay đổi.")


if __name__ == "__main__":
    main()
