"""
Interactive 1-Step YouTube OAuth Setup for Channel 2.
Takes Client Secret in terminal, generates credentials/client_secrets.json,
and initiates the one-time browser login.
"""
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_DIR = WORKSPACE_ROOT / "credentials"
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
SECRETS_FILE = CREDENTIALS_DIR / "client_secrets.json"

DEFAULT_CLIENT_ID = "378552603797-41lqhbdp5k0hjh044ltq48p0krf2sab6.apps.googleusercontent.com"
PROJECT_ID = "creatorops-youtube"

def main():
    print("=" * 60)
    print("🔑 CHANNEL 2 YOUTUBE OAUTH SETUP")
    print(f"📌 Client ID: {DEFAULT_CLIENT_ID} (Sam)")
    print("=" * 60)
    
    secret = input("\n👉 Paste your Client Secret (GOCSPX-...) here and press Enter: ").strip()
    if not secret:
        print("❌ Error: Client secret cannot be empty!")
        return 1
        
    # Build Google OAuth client secrets format
    data = {
        "installed": {
            "client_id": DEFAULT_CLIENT_ID,
            "project_id": PROJECT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": secret,
            "redirect_uris": ["http://localhost", "http://localhost:8080"]
        }
    }
    
    SECRETS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"\n✅ Created: {SECRETS_FILE}")
    print("🚀 Opening browser for authorization...\n")
    
    # Import and run uploader auth
    from fleet_engines.channel_2.youtube_uploader import get_authenticated_service
    get_authenticated_service()
    print("\n🎉 [ALL DONE] Channel 2 YouTube authorization successfully linked!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
