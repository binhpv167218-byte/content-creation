#!/usr/bin/env python3
"""
TikTok Content Posting — OAuth + post photo/video.

Usage:
  # Step 1: Get access token (one-time, saves to .env)
  python3 scripts/tiktok_post.py auth

  # Step 2: Post a photo
  python3 scripts/tiktok_post.py photo posts/060-slug/image.png --caption "Caption text #hashtag"

  # Step 3: Post a video
  python3 scripts/tiktok_post.py video path/to/video.mp4 --caption "Caption text"
"""

import argparse
import base64
import json
import os
import secrets
import sys
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import requests

# ── Config ──────────────────────────────────────────────────────────────────

ENV_FILE = Path(__file__).parent.parent / ".env"


def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def save_env_key(key, value):
    text = ENV_FILE.read_text()
    if f"{key}=" in text:
        lines = []
        for line in text.splitlines():
            if line.startswith(f"{key}="):
                lines.append(f"{key}={value}")
            else:
                lines.append(line)
        ENV_FILE.write_text("\n".join(lines) + "\n")
    else:
        with ENV_FILE.open("a") as f:
            f.write(f"\n{key}={value}\n")


env = load_env()
CLIENT_KEY = env.get("TIKTOK_CLIENT_KEY", "")
CLIENT_SECRET = env.get("TIKTOK_CLIENT_SECRET", "")
REDIRECT_URI = env.get("TIKTOK_REDIRECT_URI", "https://symphony5.netlify.app/callback")
ACCESS_TOKEN = env.get("TIKTOK_ACCESS_TOKEN", "")

SCOPES = "user.info.basic,video.publish,video.upload"
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
POST_PHOTO_URL = "https://open.tiktokapis.com/v2/post/publish/content/init/"
POST_VIDEO_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
POST_VIDEO_UPLOAD_URL = "https://open.tiktokapis.com/v2/post/publish/video/upload/"
POST_STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

# ── Auth ─────────────────────────────────────────────────────────────────────


def cmd_auth():
    state = secrets.token_hex(16)
    params = {
        "client_key": CLIENT_KEY,
        "response_type": "code",
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "state": state,
    }
    url = AUTH_URL + "?" + urlencode(params)
    print(f"\nMở browser để authorize TikTok...")
    print(f"URL: {url}\n")
    webbrowser.open(url)

    print("Sau khi authorize, TikTok redirect về symphony5.netlify.app/callback?code=XXXX")
    print("Copy toàn bộ URL từ address bar, paste vào đây:")
    callback_url = input("URL: ").strip()

    parsed = urlparse(callback_url)
    qs = parse_qs(parsed.query)
    code = qs.get("code", [None])[0]
    if not code:
        # Try if user just pasted the code directly
        code = callback_url.strip()

    print(f"\nCode: {code[:20]}...")
    token = exchange_code(code)
    save_env_key("TIKTOK_ACCESS_TOKEN", token["access_token"])
    if token.get("refresh_token"):
        save_env_key("TIKTOK_REFRESH_TOKEN", token["refresh_token"])
    print(f"\nAccess token saved to .env")
    print(f"Open ID: {token.get('open_id')}")
    print(f"Expires in: {token.get('expires_in')} seconds ({token.get('expires_in', 0)//3600}h)")


def exchange_code(code):
    resp = requests.post(TOKEN_URL, data={
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=30)
    data = resp.json()
    if "access_token" not in data and "data" in data:
        data = data["data"]
    if "access_token" not in data:
        print(f"Token exchange failed: {json.dumps(data, indent=2)}")
        sys.exit(1)
    return data

# ── Photo post ───────────────────────────────────────────────────────────────


def cmd_photo(image_path, caption):
    token = ACCESS_TOKEN or env.get("TIKTOK_ACCESS_TOKEN", "")
    if not token:
        print("No access token. Run: python3 scripts/tiktok_post.py auth")
        sys.exit(1)

    path = Path(image_path)
    if not path.exists():
        print(f"File not found: {image_path}")
        sys.exit(1)

    # Encode image as base64
    img_data = path.read_bytes()
    b64 = base64.b64encode(img_data).decode()
    mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"

    payload = {
        "post_info": {
            "title": caption,
            "privacy_level": "SELF_ONLY",  # Change to PUBLIC_TO_EVERYONE for real posts
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "photo_cover_index": 0,
            "photo_images": [f"data:{mime};base64,{b64}"],
        },
        "media_type": "PHOTO",
        "post_mode": "DIRECT_POST",
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    print(f"Posting photo: {path.name}")
    resp = requests.post(POST_PHOTO_URL, json=payload, headers=headers, timeout=60)
    data = resp.json()
    print(json.dumps(data, indent=2))

    publish_id = data.get("data", {}).get("publish_id")
    if publish_id:
        print(f"\nPublish ID: {publish_id}")
        poll_status(token, publish_id)

# ── Video post ───────────────────────────────────────────────────────────────


def cmd_video(video_path, caption):
    token = ACCESS_TOKEN or env.get("TIKTOK_ACCESS_TOKEN", "")
    if not token:
        print("No access token. Run: python3 scripts/tiktok_post.py auth")
        sys.exit(1)

    path = Path(video_path)
    if not path.exists():
        print(f"File not found: {video_path}")
        sys.exit(1)

    file_size = path.stat().st_size
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    # Init upload
    payload = {
        "post_info": {
            "title": caption,
            "privacy_level": "SELF_ONLY",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size,
            "total_chunk_count": 1,
        },
        "post_mode": "DIRECT_POST",
        "media_type": "VIDEO",
    }

    print(f"Initializing video upload: {path.name} ({file_size/1024/1024:.1f} MB)")
    resp = requests.post(POST_VIDEO_INIT_URL, json=payload, headers=headers, timeout=30)
    data = resp.json()
    print(json.dumps(data, indent=2))

    upload_url = data.get("data", {}).get("upload_url")
    publish_id = data.get("data", {}).get("publish_id")

    if not upload_url:
        print("No upload URL returned")
        sys.exit(1)

    # Upload video
    print(f"Uploading video...")
    video_data = path.read_bytes()
    upload_resp = requests.put(
        upload_url,
        data=video_data,
        headers={
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{file_size-1}/{file_size}",
            "Content-Length": str(file_size),
        },
        timeout=300,
    )
    print(f"Upload status: {upload_resp.status_code}")

    if publish_id:
        poll_status(token, publish_id)


def poll_status(token, publish_id, max_wait=120):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"}
    print(f"\nPolling status for publish_id: {publish_id}")
    for i in range(max_wait // 5):
        resp = requests.post(POST_STATUS_URL, json={"publish_id": publish_id}, headers=headers, timeout=30)
        data = resp.json()
        status = data.get("data", {}).get("status", "unknown")
        print(f"  [{i*5}s] Status: {status}")
        if status in ("PUBLISH_COMPLETE", "SUCCESS"):
            print("Published successfully!")
            return
        if status in ("FAILED", "ERROR"):
            print(f"Failed: {json.dumps(data, indent=2)}")
            return
        time.sleep(5)
    print("Timeout waiting for publish status")

# ── CLI ──────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("auth", help="OAuth login — get access token")

    p_photo = sub.add_parser("photo", help="Post a photo")
    p_photo.add_argument("image", help="Path to image file")
    p_photo.add_argument("--caption", default="", help="Post caption")

    p_video = sub.add_parser("video", help="Post a video")
    p_video.add_argument("video", help="Path to video file")
    p_video.add_argument("--caption", default="", help="Post caption")

    args = parser.parse_args()

    if args.cmd == "auth":
        cmd_auth()
    elif args.cmd == "photo":
        cmd_photo(args.image, args.caption)
    elif args.cmd == "video":
        cmd_video(args.video, args.caption)
    else:
        parser.print_help()
