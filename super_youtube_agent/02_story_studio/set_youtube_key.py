#!/usr/bin/env python3
"""Securely add a YouTube Data API key to this project's local .env file.

The key is read with terminal echo disabled and is never printed.
"""
from __future__ import annotations

import getpass
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
EXAMPLE_PATH = ROOT / ".env.example"


def main() -> int:
    if not ENV_PATH.exists():
        if not EXAMPLE_PATH.exists():
            print("Missing .env.example; run this from the CreatorOps project folder.")
            return 1
        shutil.copyfile(EXAMPLE_PATH, ENV_PATH)

    try:
        key = getpass.getpass("Paste YouTube Data API key (input hidden): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nNo key saved.")
        return 1
    except Exception:
        print("Could not read the key securely in this terminal. No key saved.")
        return 1

    if not key:
        print("Empty key; no changes made.")
        return 1

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    updated = False
    for index, line in enumerate(lines):
        if line.strip().startswith("YOUTUBE_DATA_API_KEY="):
            lines[index] = f"YOUTUBE_DATA_API_KEY={key}"
            updated = True
            break
    if not updated:
        lines.insert(0, f"YOUTUBE_DATA_API_KEY={key}")

    temp_path = ENV_PATH.with_suffix(".env.tmp")
    temp_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(temp_path, 0o600)
    except OSError:
        pass
    temp_path.replace(ENV_PATH)
    try:
        os.chmod(ENV_PATH, 0o600)
    except OSError:
        pass
    print("Saved YOUTUBE_DATA_API_KEY to the ignored local .env file. The key was not displayed.")
    print("Restart CreatorOps to load it; do not share .env or screenshots containing the key.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
