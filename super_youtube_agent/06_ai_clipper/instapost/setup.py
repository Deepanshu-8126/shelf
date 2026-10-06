#!/usr/bin/env python3
"""Instagram credentials safely .env mein daalne ke liye.

Ise TUM chalao. Jo type karoge wo screen pe nahi dikhega, chat mein nahi
jayega, kisi log mein nahi aayega -- seedha /home/user/autoclip/.env mein
chmod 600 ke saath likha jayega.

    python3 /home/user/instapost/setup.py

Dhyaan do: ye sirf OFFICIAL Graph API ke credentials maangta hai
(IG_USER_ID + IG_ACCESS_TOKEN). Password yahan bhi nahi maanga jaata,
kyunki password wala rasta hi ban wala rasta hai.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

ENV = Path("/home/user/autoclip/.env")


def put(key: str, value: str) -> None:
    """Replace or append KEY=value, leaving every other line untouched."""
    lines = ENV.read_text().splitlines() if ENV.exists() else []
    out, done = [], False
    for line in lines:
        if line.strip().startswith(f"{key}="):
            out.append(f"{key}={value}")
            done = True
        else:
            out.append(line)
    if not done:
        out.append(f"{key}={value}")
    ENV.parent.mkdir(parents=True, exist_ok=True)
    ENV.write_text("\n".join(out).rstrip() + "\n")
    ENV.chmod(0o600)


def main() -> int:
    print("Instagram setup (official Graph API)\n")
    print("Ye chahiye - dono developers.facebook.com se milte hain:")
    print("  1. Instagram user ID  (sirf number hai, secret nahi)")
    print("  2. Access token       (SECRET - type karoge, dikhega nahi)\n")

    uid = input("IG_USER_ID: ").strip()
    if not uid.isdigit():
        print("user ID sirf number hona chahiye. Ruk gaya.")
        return 1

    token = getpass.getpass("IG_ACCESS_TOKEN (chhupa rahega): ").strip()
    if len(token) < 20:
        print("token bahut chhota lag raha hai. Ruk gaya.")
        return 1

    put("IG_USER_ID", uid)
    put("IG_ACCESS_TOKEN", token)

    # Kabhi value print mat karo -- sirf itna ki kaam ho gaya.
    print(f"\nliya gaya. {ENV} mein likh diya (chmod 600, git mein nahi jaata).")
    print(f"  IG_USER_ID       = {uid}")
    print(f"  IG_ACCESS_TOKEN  = {'*' * 12} ({len(token)} characters)")
    print("\nAb dashboard restart karo, Instagram button chal jayega.")
    print("Check karne ke liye:  python3 -m instapost.cli --help")
    return 0


if __name__ == "__main__":
    sys.exit(main())
