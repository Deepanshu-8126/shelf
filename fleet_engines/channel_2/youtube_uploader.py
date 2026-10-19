"""
Channel 2 YouTube Auto-Uploader (YouTube Data API v3).
Supports:
  1. Automatic OAuth token exchange via client_secrets.json
  2. One-time browser authorization with auto-refreshing token.json
  3. Uploads 9:16 Shorts with title, description, tags, category, and privacy status
  4. Supports 'unlisted' mode by default for safe pre-publish review
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]
CREDENTIALS_DIR = WORKSPACE_ROOT / "credentials"
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

CLIENT_SECRETS_FILE = CREDENTIALS_DIR / "client_secrets.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"

# Check root fallback
if not CLIENT_SECRETS_FILE.exists() and (WORKSPACE_ROOT / "client_secrets.json").exists():
    CLIENT_SECRETS_FILE = WORKSPACE_ROOT / "client_secrets.json"

def _auto_decode_env_credentials(channel: int = 2):
    """Decodes base64 credentials from environment variables if present."""
    import base64
    yt_client_b64 = os.getenv("YT_CLIENT_B64", "").strip()
    if yt_client_b64 and not CLIENT_SECRETS_FILE.exists():
        try:
            CLIENT_SECRETS_FILE.write_bytes(base64.b64decode(yt_client_b64))
            print(f"✅ Decoded client_secrets.json from YT_CLIENT_B64 env", flush=True)
        except Exception as e:
            print(f"⚠️ Failed to decode YT_CLIENT_B64: {e}", flush=True)

    target_token = CREDENTIALS_DIR / f"channel_{channel}_token.json"
    yt_token_b64 = (
        os.getenv(f"YT_TOKEN_CH{channel}_B64")
        or os.getenv("YT_TOKEN_CH2_B64")
        or os.getenv("YT_TOKEN_B64")
        or ""
    ).strip()
    if yt_token_b64 and not target_token.exists():
        try:
            target_token.write_bytes(base64.b64decode(yt_token_b64))
            if not TOKEN_FILE.exists():
                TOKEN_FILE.write_bytes(base64.b64decode(yt_token_b64))
            print(f"✅ Decoded channel_{channel}_token.json from env", flush=True)
        except Exception as e:
            print(f"⚠️ Failed to decode YT_TOKEN_CH{channel}_B64: {e}", flush=True)

    yt_token_raw = os.getenv("YOUTUBE_TOKEN_JSON", "").strip()
    if yt_token_raw and not TOKEN_FILE.exists():
        try:
            TOKEN_FILE.write_text(yt_token_raw, encoding="utf-8")
            print(f"✅ Restored token.json from YOUTUBE_TOKEN_JSON env", flush=True)
        except Exception as e:
            print(f"⚠️ Failed to write YOUTUBE_TOKEN_JSON: {e}", flush=True)

def get_authenticated_service(channel: int = 2):
    """Returns authenticated YouTube API v3 service for specific channel (1, 2, or 3)."""
    _auto_decode_env_credentials(channel)
    
    # Check channel-specific token, or fallback to global token.json
    target_token = CREDENTIALS_DIR / f"channel_{channel}_token.json"
    if not target_token.exists() and TOKEN_FILE.exists():
        target_token = TOKEN_FILE
        
    creds = None
    if target_token.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(target_token), SCOPES)
        except Exception as e:
            print(f"⚠️ Token file invalid, re-authenticating: {e}")
            
    # If no valid credentials, run local OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print(f"🔄 Refreshing expired YouTube OAuth token for Channel {channel}...", flush=True)
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS_FILE.exists():
                raise FileNotFoundError(
                    f"❌ client_secrets.json not found!\n"
                    f"Please place your Google Cloud OAuth client secrets JSON file at:\n"
                    f"👉 {CLIENT_SECRETS_FILE}\n"
                    f"Or set YT_CLIENT_B64 / YT_TOKEN_B64 in your environment / .env file."
                )
            print(f"🔑 Opening browser for one-time YouTube Channel {channel} authorization...", flush=True)
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(port=8080)
            
        # Save token for future automatic runs
        target_token.write_text(creds.to_json(), encoding="utf-8")
        print(f"✅ Saved persistent YouTube token for Channel {channel} to {target_token}", flush=True)
        
    return build("youtube", "v3", credentials=creds)

def upload_short_to_youtube(
    video_path: Path,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    privacy_status: str = "unlisted",
    channel: int = 2
) -> Dict[str, Any]:
    """
    Uploads a short to YouTube via API v3 for channel 1 or 2.
    privacy_status can be: 'public', 'unlisted', or 'private'.
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
        
    tags = tags or ["shorts", "mystery", "facts", "viral", "reddit"]
    youtube = get_authenticated_service(channel=channel)
    
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:30],
            "categoryId": "27"  # Education / Science / Mystery
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }
    
    print(f"📤 Uploading '{video_path.name}' to YouTube ({privacy_status.upper()})...", flush=True)
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"⏳ Upload progress: {int(status.progress() * 100)}%", flush=True)
            
    video_id = response.get("id")
    video_url = f"https://youtu.be/{video_id}"
    print("=" * 70, flush=True)
    print(f"🎉 [YOUTUBE UPLOAD COMPLETE]")
    print(f"🔗 Video URL: {video_url}")
    print(f"🔒 Privacy: {privacy_status.upper()}")
    print("=" * 70, flush=True)
    return {"video_id": video_id, "video_url": video_url, "response": response}

def get_connected_channel_info() -> Dict[str, Any]:
    """Queries and displays which YouTube channel is authorized."""
    youtube = get_authenticated_service()
    res = youtube.channels().list(mine=True, part="snippet,statistics").execute()
    items = res.get("items", [])
    if not items:
        print("⚠️ No YouTube channel found for this authorized account.")
        return {}
    
    ch = items[0]
    title = ch["snippet"].get("title", "Unknown")
    custom_url = ch["snippet"].get("customUrl", "N/A")
    channel_id = ch.get("id", "N/A")
    subscribers = ch["statistics"].get("subscriberCount", "0")
    video_count = ch["statistics"].get("videoCount", "0")
    
    print("\n" + "=" * 65)
    print("📺 CONNECTED YOUTUBE CHANNEL INFO:")
    print(f"  • Name        : {title}")
    print(f"  • Handle      : {custom_url}")
    print(f"  • Channel ID  : {channel_id}")
    print(f"  • Subscribers : {subscribers}")
    print(f"  • Videos      : {video_count}")
    print("=" * 65 + "\n")
    return {"title": title, "custom_url": custom_url, "channel_id": channel_id}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="YouTube Uploader for Channel 2")
    parser.add_argument("--auth", action="store_true", help="Run one-time OAuth authentication")
    parser.add_argument("--check-channel", action="store_true", help="Check which channel is currently connected")
    parser.add_argument("--video", type=str, default="", help="Path to MP4 video")
    parser.add_argument("--title", type=str, default="Mystery Short #shorts", help="Video Title")
    parser.add_argument("--privacy", type=str, default="unlisted", choices=["public", "unlisted", "private"])
    args = parser.parse_args()
    
    if args.auth:
        get_authenticated_service()
        print("✅ OAuth Authentication test passed!")
        try:
            get_connected_channel_info()
        except Exception:
            pass
    elif args.check_channel:
        get_connected_channel_info()
    elif args.video:
        upload_short_to_youtube(Path(args.video), args.title, "Uploaded via Channel 2 Engine", privacy_status=args.privacy)
    else:
        print("Run with `--auth` to connect your channel, `--check-channel` to view channel details, or `--video <path>` to upload.")
