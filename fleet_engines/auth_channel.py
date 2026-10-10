"""
Universal Channel Authorizer for Fleet Channels (Channel 1 & Channel 2).
Saves separate dedicated OAuth tokens:
  - credentials/channel_1_token.json (Reddit Drama & Confessions)
  - credentials/channel_2_token.json (Hindi Vox Mysteries)
"""
import os
import sys
import json
import argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_DIR = WORKSPACE_ROOT / "credentials"
CLIENT_SECRETS = CREDENTIALS_DIR / "client_secrets.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def authorize_channel(channel_num: int):
    token_file = CREDENTIALS_DIR / f"channel_{channel_num}_token.json"
    
    if not CLIENT_SECRETS.exists():
        print(f"❌ Error: client_secrets.json not found at {CLIENT_SECRETS}")
        return 1
        
    print("=" * 65)
    print(f"🔑 AUTHORIZING YOUTUBE FOR CHANNEL {channel_num}")
    if channel_num == 1:
        print("📌 Target: Channel 1 (Viral Reddit Drama & Confessions Shorts)")
    elif channel_num == 2:
        print("📌 Target: Channel 2 (Hinglish Vox Mystery & Documentaries)")
    print(f"📁 Token will be saved to: {token_file}")
    print("=" * 65)
    print("\n🌐 Opening browser... Select the YouTube Channel for Channel " + str(channel_num))
    
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    
    # Save token for this channel
    token_file.write_text(creds.to_json(), encoding="utf-8")
    print(f"\n✅ Saved dedicated token to {token_file}")
    
    # Inspect channel name
    try:
        yt = build("youtube", "v3", credentials=creds)
        res = yt.channels().list(mine=True, part="snippet,statistics").execute()
        items = res.get("items", [])
        if items:
            ch = items[0]
            print("\n📺 CONNECTED CHANNEL:")
            print(f"  • Name   : {ch['snippet'].get('title')}")
            print(f"  • Handle : {ch['snippet'].get('customUrl', 'N/A')}")
            print(f"  • ID     : {ch.get('id')}")
            print(f"  • Videos : {ch['statistics'].get('videoCount')}")
    except Exception as e:
        print(f"⚠️ Could not fetch channel metadata: {e}")
        
    print("\n🎉 Channel " + str(channel_num) + " successfully linked!\n")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fleet Channel YouTube Authorizer")
    parser.add_argument("--channel", type=int, default=1, choices=[1, 2], help="Channel slot (1 or 2)")
    args = parser.parse_args()
    
    authorize_channel(args.channel)
