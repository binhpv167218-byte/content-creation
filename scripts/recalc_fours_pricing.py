#!/usr/bin/env python3
"""Recalculate FourS Tower pricing using official formulas from phiếu tính giá."""

import os, requests, math
from dotenv import load_dotenv

load_dotenv('/Users/macos/Desktop/content-creation/.env')

API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = os.getenv('AIRTABLE_BASE_ID')
TABLE_ID = 'tblyJ7vOHHHGJPZ10'

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# Official formulas from phiếu tính giá:
# Base (chưa VAT) = Niêm yết / 1.12
# CK Early Bird 5% → After EB = Base × 0.95
# Giá Có Vay    = After EB × 1.12 = Niêm yết × 0.95
# Giá Không Vay = After EB × 0.95 × 1.12 = Niêm yết × 0.9025
# Giá TTS 95%   = After EB × 0.95 × 0.835 × 1.12 = Niêm yết × 0.753588

RATIO_CO_VAY   = 0.95
RATIO_KO_VAY   = 0.9025
RATIO_TTS      = 0.9025 * 0.835  # = 0.753588 (trước VAT) → ×1.12 → ×0.844018...
# Correct: TTS = After EB+KV × (1-0.165) × 1.12
# After EB+KV = Base × 0.95 × 0.95
# TTS = Base × 0.95 × 0.95 × 0.835 × 1.12
# = (Niêm yết/1.12) × 0.9025 × 0.835 × 1.12
# = Niêm yết × 0.9025 × 0.835
RATIO_TTS_FINAL = 0.9025 * 0.835  # = 0.753588

def round_million(val):
    return round(val / 1_000_000) * 1_000_000

def get_all_records():
    records = []
    offset = None
    while True:
        url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'
        params = {'pageSize': 100}
        if offset:
            params['offset'] = offset
        r = requests.get(url, headers=HEADERS, params=params)
        data = r.json()
        records.extend(data.get('records', []))
        offset = data.get('offset')
        if not offset:
            break
    return records

def patch_records(updates):
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}'
    # Batch 10
    for i in range(0, len(updates), 10):
        batch = updates[i:i+10]
        payload = {'records': batch}
        r = requests.patch(url, headers=HEADERS, json=payload)
        if r.status_code != 200:
            print(f'ERROR batch {i//10+1}: {r.status_code} {r.text[:200]}')
        else:
            print(f'  OK batch {i//10+1} ({len(batch)} records)')

def main():
    print('Fetching all FourS Tower records...')
    records = get_all_records()
    print(f'Found {len(records)} records')

    updates = []
    skipped = 0

    for rec in records:
        fields = rec.get('fields', {})
        niem_yet = fields.get('Giá VAT+KPBT')
        ma_can = fields.get('Mã Căn', '?')

        if not niem_yet:
            print(f'  SKIP {ma_can} — no Giá VAT+KPBT')
            skipped += 1
            continue

        co_vay   = round_million(niem_yet * RATIO_CO_VAY)
        ko_vay   = round_million(niem_yet * RATIO_KO_VAY)
        tts_95   = round_million(niem_yet * RATIO_TTS_FINAL)

        updates.append({
            'id': rec['id'],
            'fields': {
                'Giá Có Vay':   co_vay,
                'Giá Không Vay': ko_vay,
                'Giá TTS 95%':  tts_95,
            }
        })

        print(f'  {ma_can}: NY={niem_yet/1e6:.2f}M → CoVay={co_vay/1e6:.2f}M | KoVay={ko_vay/1e6:.2f}M | TTS={tts_95/1e6:.2f}M')

    print(f'\nPrepared {len(updates)} updates, {skipped} skipped')
    print('Patching Airtable...')
    patch_records(updates)
    print('Done.')

if __name__ == '__main__':
    main()
