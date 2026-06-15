#!/usr/bin/env python3
"""Lấy token mới với quyền đọc + ghi Google Drive."""
import json, warnings
warnings.filterwarnings('ignore')

from google_auth_oauthlib.flow import InstalledAppFlow

KEYS_FILE  = '/Users/macos/.npm-global/lib/node_modules/gcp-oauth.keys.json'
TOKEN_OUT  = '/Users/macos/.config/gdrive-rw-token.json'

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
]

flow = InstalledAppFlow.from_client_secrets_file(KEYS_FILE, scopes=SCOPES)
creds = flow.run_local_server(port=0)

token_data = {
    'access_token':  creds.token,
    'refresh_token': creds.refresh_token,
    'token_uri':     creds.token_uri,
    'client_id':     creds.client_id,
    'client_secret': creds.client_secret,
    'scopes':        list(creds.scopes),
}
with open(TOKEN_OUT, 'w') as f:
    json.dump(token_data, f, indent=2)

print(f"Token đã lưu: {TOKEN_OUT}")
