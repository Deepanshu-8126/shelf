#!/usr/bin/env python3
"""
Bridge launcher for Google Pro Veo Studio from facts_yt workspace.
Delegates to D:/affi;ate/trend-earning-system/run_google_pro_veo.py
"""
import sys
import subprocess
from pathlib import Path

AFFILIATE_DIR = Path("D:/affi;ate/trend-earning-system")
RUNNER = AFFILIATE_DIR / "run_google_pro_veo.py"

if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        cmd = [sys.executable, str(RUNNER)] + args
        subprocess.run(cmd, cwd=str(AFFILIATE_DIR))
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
