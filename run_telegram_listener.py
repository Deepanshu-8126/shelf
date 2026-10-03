#!/usr/bin/env python3
"""
Bridge launcher for Telegram Phone Controller from facts_yt workspace.
Delegates to D:/affi;ate/trend-earning-system/run_telegram_listener.py
"""
import sys
import subprocess
from pathlib import Path

AFFILIATE_DIR = Path("D:/affi;ate/trend-earning-system")
RUNNER = AFFILIATE_DIR / "run_telegram_listener.py"

if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        cmd = [sys.executable, str(RUNNER)] + args
        subprocess.run(cmd, cwd=str(AFFILIATE_DIR))
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
