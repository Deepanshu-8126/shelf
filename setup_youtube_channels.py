"""
Multi-Channel YouTube OAuth & GitHub Secrets Generator
Usage:
    python setup_youtube_channels.py
"""
import base64
import json
import os
import sys
from pathlib import Path

# Fix UTF-8 encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CRED_DIR = Path("super_youtube_agent/01_facts_shorts/credentials")
CRED_DIR.mkdir(parents=True, exist_ok=True)
CLIENT_SECRET_PATH = CRED_DIR / "client_secret.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def file_to_b64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def run_auth_for_channel(channel_name: str, output_token_path: Path):
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not CLIENT_SECRET_PATH.exists():
        print(f"\n❌ Error: '{CLIENT_SECRET_PATH}' not found!")
        print("👉 Please download OAuth client credentials from Google Cloud Console")
        print(f"👉 And save it as: {CLIENT_SECRET_PATH.resolve()}\n")
        return False

    print(f"\n🌐 Opening browser for YouTube Authentication: [{channel_name}]...")
    print("⚠️ Important: Login with the specific Google Account that owns this YouTube channel.")
    
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

    with open(output_token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"✅ Successfully authenticated! Token saved to: {output_token_path}")
    return True


def main():
    print("=" * 65)
    print("🎬 YouTube Studio Multi-Channel Setup & GitHub Secrets Helper")
    print("=" * 65)
    print("Channels available in your codebase:")
    print("  1. Channel 1: Viral Facts Shorts (FactShorts)")
    print("  2. Channel 2: History & Unsolved Mysteries (Story Studio)")
    print("  3. Channel 3: Vox Documentary & Geopolitics (Global Ledger)")
    print("  4. Channel 4: Lofi Music Studio")
    print("  5. Channel 5: Deep Dark Sutra")
    print("  6. Channel 6: AI Clipper")
    print("  7. Channel 7: Coding & Tech Studio (New)")
    print("=" * 65)

    if not CLIENT_SECRET_PATH.exists():
        print(f"\n⚠️  Step 1 Missing: Place your Google Cloud 'client_secret.json' file inside:")
        print(f"   📁 {CRED_DIR.resolve()}/client_secret.json")
        print("\nOnce placed, run this script again: python setup_youtube_channels.py")
        return

    client_b64 = file_to_b64(CLIENT_SECRET_PATH)
    print(f"\n🔑 Common Client Secret GitHub Secret (Use for all channels):")
    print(f"Name:  YT_CLIENT_B64")
    print(f"Value: {client_b64[:40]}... (Total {len(client_b64)} chars)\n")

    print("Which channel do you want to authenticate right now?")
    print("  [1] Channel 1 (Facts Shorts)")
    print("  [2] Channel 2 (Story & Mysteries)")
    print("  [7] Channel 7 (Coding & Tech)")
    print("  [A] Authenticate ALL one by one")
    print("  [S] Show existing GitHub Secrets values")
    
    choice = input("\nEnter choice (1/2/7/A/S): ").strip().upper()

    tokens = {
        "1": ("Channel 1 (Facts)", CRED_DIR / "token.json", "YT_TOKEN_B64"),
        "2": ("Channel 2 (Story & Mysteries)", CRED_DIR / "token_ch2.json", "YT_TOKEN_CH2_B64"),
        "7": ("Channel 7 (Coding & Tech)", CRED_DIR / "token_coding.json", "YT_TOKEN_CODING_B64"),
    }

    if choice in tokens:
        name, path, secret_name = tokens[choice]
        if run_auth_for_channel(name, path):
            b64_val = file_to_b64(path)
            print("\n" + "=" * 65)
            print(f"📋 Copy this into GitHub Repository Settings -> Secrets -> Actions:")
            print(f"SECRET NAME : {secret_name}")
            print(f"SECRET VALUE:\n{b64_val}")
            print("=" * 65)

    elif choice == "A":
        for k, (name, path, secret_name) in tokens.items():
            print(f"\n---> Starting Auth for {name} <---")
            if run_auth_for_channel(name, path):
                b64_val = file_to_b64(path)
                print(f"Secret Name: {secret_name}\nValue:\n{b64_val}\n")

    elif choice == "S":
        print("\n=== Existing Saved Tokens & Secrets ===")
        print(f"1. YT_CLIENT_B64:\n{client_b64}\n")
        for k, (name, path, secret_name) in tokens.items():
            if path.exists():
                print(f"2. {secret_name} ({name}):\n{file_to_b64(path)}\n")
            else:
                print(f"2. {secret_name} ({name}): ⚠️ Not generated yet. Run auth first.")


if __name__ == "__main__":
    main()
