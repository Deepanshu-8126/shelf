@echo off
setlocal enabledelayedexpansion
title Multi-Channel AI YouTube Studio Master Hub
color 0A

:menu
cls
echo ================================================================
echo        🚀 MULTI-CHANNEL AI YOUTUBE STUDIO MASTER HUB
echo ================================================================
echo.
echo   [1] 🔵 Channel 1 — Viral Facts Shorts (Space & Science)
echo   [2] 🔴 Channel 2 — Story & Mysteries Studio (Historical Cases)
echo   [3] 🟢 Channel 3 — Vox & Geopolitics Studio (Map Documentaries)
echo   [4] 🟣 Channel 4 — Lofi 24/7 Music Studio (Ambient Beats)
echo   [5] 🕵️ Channel 5 — Dark Sutra Crime Studio (True Crime & Paranormal)
echo   [6] ✂️ Channel 6 — AI Auto Clipper Best (Viral Podcast Cuts)
echo   [7] 💻 Channel 7 — Coding & Tech Studio (Code Hacks & AI Tools)
echo.
echo   [C] 🎬 Start ComfyUI + Wan 2.2 Local GPU Server (Dark Sutra)
echo   [T] 📱 Send Telegram Connection Test Ping to All Channels
echo   [0] ❌ Exit
echo.
echo ================================================================
set /p choice="Select Option [1-7, C, T, 0]: "

if "%choice%"=="1" (
    echo.
    echo Launching Channel 1: Viral Facts Shorts...
    cd super_youtube_agent\01_facts_shorts
    python main.py --generate --mode facts
    cd ..\..
    pause
    goto menu
)
if "%choice%"=="2" (
    echo.
    echo Launching Channel 2: Story & Mysteries Studio...
    cd super_youtube_agent\01_facts_shorts
    python main.py --generate --niche history --mode story
    cd ..\..
    pause
    goto menu
)
if "%choice%"=="3" (
    echo.
    echo Launching Channel 3: Vox & Geopolitics Studio...
    cd super_youtube_agent\03_vox_studio
    python cli.py trends --limit 3 --auto-produce
    cd ..\..
    pause
    goto menu
)
if "%choice%"=="4" (
    echo.
    echo Launching Channel 4: Lofi 24/7 Music Studio...
    cd super_youtube_agent\04_lofi_studio
    python -m main
    cd ..\..
    pause
    goto menu
)
if "%choice%"=="5" (
    echo.
    echo ================================================================
    echo  🕵️ CHANNEL 5: DARK SUTRA CRIME STUDIO (INVESTIGATIVE ENGINE)
    echo ================================================================
    set /p dark_topic="Enter Crime/Mystery Topic (Press Enter for 'Burari Deaths'): "
    if "!dark_topic!"=="" set "dark_topic=Burari Deaths"
    cd super_youtube_agent\05_dark_sutra
    python main.py --topic "!dark_topic!" --format short --lang hindi --voice hm_omega
    cd ..\..
    pause
    goto menu
)
if /i "%choice%"=="C" (
    echo.
    echo Launching ComfyUI + Wan 2.2 Server...
    call super_youtube_agent\05_dark_sutra\scripts\start_comfyui_wan.bat
    pause
    goto menu
)
if "%choice%"=="6" (
    echo.
    echo Launching Channel 6: AI Auto Clipper Best...
    cd super_youtube_agent\06_ai_clipper
    python main.py
    cd ..\..
    pause
    goto menu
)
if "%choice%"=="7" (
    echo.
    echo Launching Channel 7: Coding & Tech Studio...
    cd super_youtube_agent\07_coding_studio
    python main.py --generate --niche coding --mode story
    cd ..\..
    pause
    goto menu
)
if /i "%choice%"=="T" (
    echo.
    echo Sending test pings to Telegram...
    python send_to_telegram.py --test "Channel 1 (Space & Science - FactShorts)"
    python send_to_telegram.py --test "Channel 2 (Story & Mysteries Studio)"
    python send_to_telegram.py --test "Channel 3 (Vox & Geopolitics Studio)"
    python send_to_telegram.py --test "Channel 5 (Dark Sutra Crime Studio)"
    python send_to_telegram.py --test "Channel 7 (Coding & Tech Studio)"
    pause
    goto menu
)
if "%choice%"=="0" exit /b 0

echo Invalid selection.
pause
goto menu
