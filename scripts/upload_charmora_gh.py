#!/usr/bin/env python3
"""Upload Giỏ Hàng Charmora Onsen 3 lên Airtable."""
import json, os, sys, requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# ── 1. Tạo table ──────────────────────────────────────────────────────────────
TABLE_NAME = "🏠 GH Charmora Onsen 3"

create_payload = {
    "name": TABLE_NAME,
    "fields": [
        {"name": "Mã Căn",           "type": "singleLineText"},
        {"name": "Loại Căn",         "type": "singleSelect",
         "options": {"choices": [
             {"name": "STU",  "color": "yellowBright"},
             {"name": "1BR+", "color": "greenBright"},
             {"name": "2BR",  "color": "blueBright"},
         ]}},
        {"name": "Tầng",             "type": "number",
         "options": {"precision": 0}},
        {"name": "View",             "type": "singleLineText"},
        {"name": "Hướng",            "type": "singleSelect",
         "options": {"choices": [
             {"name": "Bắc",     "color": "blueBright"},
             {"name": "Nam",     "color": "greenBright"},
             {"name": "Đông",    "color": "tealBright"},
             {"name": "Đông Nam","color": "cyanBright"},
             {"name": "Tây",     "color": "orangeBright"},
         ]}},
        {"name": "DT Thông Thủy (m²)", "type": "number",
         "options": {"precision": 1}},
        {"name": "Giá VAT+KPBT",    "type": "currency",
         "options": {"precision": 0, "symbol": "₫"}},
        {"name": "Giá Có Vay",      "type": "currency",
         "options": {"precision": 0, "symbol": "₫"}},
        {"name": "Giá Không Vay",   "type": "currency",
         "options": {"precision": 0, "symbol": "₫"}},
        {"name": "Giá TTS 95%",     "type": "currency",
         "options": {"precision": 0, "symbol": "₫"}},
        {"name": "Tình Trạng",      "type": "singleSelect",
         "options": {"choices": [
             {"name": "Còn hàng", "color": "greenBright"},
             {"name": "Đã cọc",   "color": "yellowBright"},
             {"name": "Đã bán",   "color": "redBright"},
         ]}},
        {"name": "Nổi Bật",         "type": "checkbox",
         "options": {"color": "yellowBright", "icon": "star"}},
        {"name": "Ghi Chú",         "type": "singleLineText"},
    ]
}

r = requests.post(
    f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables",
    headers=HEADERS, json=create_payload
)
if r.status_code not in (200, 201):
    print(f"❌ Tạo table thất bại: {r.status_code} {r.text}")
    sys.exit(1)

table_id = r.json()["id"]
print(f"✅ Tạo table '{TABLE_NAME}' — ID: {table_id}")

# ── 2. Dữ liệu giỏ hàng ──────────────────────────────────────────────────────
units = [
    # mã,        loại,  tầng, view,                              hướng,    dt,   vat_kpbt,    co_vay,      ko_vay,      tts95,       ghi_chu
    ("O3.15.31", "STU",  15, "Sông Quán Trường + pháo hoa",     "Bắc",   34.4, 3295226163, 3164405684, 3006185400, 2540226662, ""),
    ("O3.16.25", "STU",  16, "Sông Tắc",                        "Tây",   34.5, 2717380625, 2609500614, 2479025584, 2073828852, ""),
    ("O3.09.15", "1BR+",  9, "Nội khu",                         "Đông",  57.3, 3303450233, 3172303258, 3013688096, 2546566442, ""),
    ("O3.09.29", "1BR+",  9, "Sông Tắc",                        "Tây",   61.0, 4273357315, 4103705030, 3898519778, 3294249212, ""),
    ("O3.15.27", "1BR+", 15, "Sông Tắc",                        "Tây",   50.4, 4010261383, 3851054007, 3658501305, 3091433602, ""),
    ("O3.16.12A","1BR+", 16, "Nội khu",                         "Đông",  59.1, 3394463848, 3259703633, 3096718452, 2616727093, ""),
    ("O3.20.18", "1BR+", 20, "Sông hướng The Charm",            "Nam",   53.7, 4810098778, 4619137857, 4388180964, 3708012915, ""),
    ("O3.20.xx", "1BR+", 20, "Sông",                            "Nam",   53.9, 5059329248, 4858470084, 4615546580, 3900136860, "Cần xác nhận mã căn"),
    ("O3.09.07", "2BR",   9, "Nội khu",                         "Đông",  74.6, 4773064965, 4583574286, 4354395372, 3679464259, ""),
    ("O3.11.30", "2BR",  11, "Sông Quán Trường + pháo hoa",     "Bắc",   76.0, 7422298180, 7127632942, 6771251296, 5721707344, ""),
    ("O3.20.24", "2BR",  20, "Sông Tắc",                        "Tây",   72.1, 6444908979, 6189046092, 5879593788, 4968256752, ""),
]

records = []
for (ma, loai, tang, view, huong, dt, vat, co_vay, ko_vay, tts95, ghi_chu) in units:
    fields = {
        "Mã Căn":             ma,
        "Loại Căn":           loai,
        "Tầng":               tang,
        "View":               view,
        "Hướng":              huong,
        "DT Thông Thủy (m²)": dt,
        "Giá VAT+KPBT":       vat,
        "Giá Có Vay":         co_vay,
        "Giá Không Vay":      ko_vay,
        "Giá TTS 95%":        tts95,
        "Tình Trạng":         "Còn hàng",
        "Nổi Bật":            False,
    }
    if ghi_chu:
        fields["Ghi Chú"] = ghi_chu
    records.append({"fields": fields})

# ── 3. Upload (batch 10) ──────────────────────────────────────────────────────
url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}"
for i in range(0, len(records), 10):
    batch = records[i:i+10]
    r = requests.post(url, headers=HEADERS,
                      json={"records": batch, "typecast": True})
    if r.status_code in (200, 201):
        print(f"✅ Upload {len(r.json()['records'])} records")
    else:
        print(f"❌ Upload thất bại: {r.status_code} {r.text}")
        sys.exit(1)

print(f"\n🎉 Xong — {len(records)} căn Charmora Onsen 3 đã lên Airtable (table ID: {table_id})")
