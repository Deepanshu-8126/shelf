from __future__ import annotations

import argparse
from pathlib import Path

from .config import ROOT, SECRETS_DIR

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Authorize one owned YouTube channel for CreatorOps")
    parser.add_argument("--channel", required=True, help="Local slot id, e.g. ch-1")
    parser.add_argument("--client-secrets", default="secrets/client_secret.json", help="OAuth client JSON downloaded from Google Cloud Console")
    args = parser.parse_args()
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise SystemExit("Install optional dependencies first: pip install -r requirements.txt") from exc
    client_file = Path(args.client_secrets)
    if not client_file.is_absolute():
        client_file = ROOT / client_file
    if not client_file.exists():
        raise SystemExit(f"OAuth client JSON not found: {client_file}\nCreate a Google Cloud OAuth Desktop client and save it there.")
    flow = InstalledAppFlow.from_client_secrets_file(str(client_file), SCOPES)
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    token_dir = SECRETS_DIR / "tokens"
    token_dir.mkdir(parents=True, exist_ok=True)
    token_file = token_dir / f"{args.channel}.json"
    token_file.write_text(credentials.to_json(), encoding="utf-8")
    print(f"Authorized token saved to {token_file.relative_to(ROOT)}")
    print("Keep secrets/ out of Git. Never paste this token into chat or a public repository.")


if __name__ == "__main__":
    main()
