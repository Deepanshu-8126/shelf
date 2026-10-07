@echo off
title Meesho to Instagram Reels Daily Autopilot - Google Veo Full-Motion
color 0B
echo ==============================================================================
echo   MEESHO TRENDING TO INSTAGRAM REELS AUTOPILOT (GOOGLE VEO 3.1 FULL-MOTION)
echo ==============================================================================
echo.

cd /d "D:\SHELF_STORE"

echo [1/2] Checking Python environment...
python -c "import sys; print('Python active:', sys.version.split()[0])"

echo.
echo [2/2] Running Daily Instagram Reel Generation & Publishing...
python scripts/autopilot_daily_reels.py --slot=auto

echo.
echo ==============================================================================
echo   AUTOPILOT RUN COMPLETED! Check D:\SHELF_STORE\data\reels_output for videos.
echo ==============================================================================
pause
