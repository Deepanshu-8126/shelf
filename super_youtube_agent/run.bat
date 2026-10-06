@echo off
set SCRIPT_DIR=%~dp0
call "%SCRIPT_DIR%super_youtube_agent\01_facts_shorts\venv\Scripts\activate.bat"

if /i "%~1"=="--help" goto help
if /i "%~1"=="-h" goto help
if /i "%~1"=="/?" goto help
if /i "%~1"=="--channel1" goto facts
if /i "%~1"=="--channel2" goto studio
if /i "%~1"=="--studio" goto studio
if /i "%~1"=="--gaming" goto studio
if /i "%~1"=="--channel3" goto dark
if /i "%~1"=="--dark" goto dark
if /i "%~1"=="--sutra" goto dark
if /i "%~1"=="--channel4" goto lofi
if /i "%~1"=="--lofi" goto lofi
if /i "%~1"=="--channel5" goto vox
if /i "%~1"=="--vox" goto vox
if /i "%~1"=="--ledger" goto vox
if /i "%~1"=="--clipper" goto clipper

:facts
cd /d "%SCRIPT_DIR%super_youtube_agent\01_facts_shorts"
echo [Channel 1: FactShorts] Viral 9:16 Facts Pipeline
if "%~1"=="" (
    echo Running demo video render...
    python main.py --demo
) else if /i "%~1"=="--channel1" (
    shift
    python main.py %1 %2 %3 %4 %5 %6
) else (
    python main.py %*
)
goto end

:studio
cd /d "%SCRIPT_DIR%super_youtube_agent\02_story_studio"
echo [Channel 2: Story Studio] Starting Web Server at http://localhost:8787...
echo Features: GTA VI Clips Lab (Hindi/Hinglish) + Market Scout + Documentary Research + Strategy Calendar
python server.py
goto end

:dark
cd /d "%SCRIPT_DIR%super_youtube_agent\03_dark_sutra"
echo [Channel 3: Dark Sutra] True Crime and Mystery Documentary Engine...
if /i "%~1"=="--channel3" shift
if /i "%~1"=="--dark" shift
if /i "%~1"=="--sutra" shift
python main.py %*
goto end

:lofi
cd /d "%SCRIPT_DIR%super_youtube_agent\04_lofi_studio"
echo [Channel 4: Lofi Studio] Starting 24/7 Lofi Ambient Pipeline...
if /i "%~1"=="--channel4" shift
if /i "%~1"=="--lofi" shift
if exist "main_lofi.py" (
    python main_lofi.py %*
) else (
    python lofi_pipeline.py %*
)
goto end

:vox
cd /d "%SCRIPT_DIR%super_youtube_agent\05_vox_ledger"
echo [Channel 5: The Global Ledger] Geopolitical Map and Investigative Explainer...
if /i "%~1"=="--channel5" shift
if /i "%~1"=="--vox" shift
if /i "%~1"=="--ledger" shift
python cli.py %*
goto end

:clipper
cd /d "%SCRIPT_DIR%super_youtube_agent\06_ai_clipper"
echo [AI Clipper Best] Auto-clipping Video Pipeline...
shift
python -m autoclip.cli %*
goto end

:help
echo =========================================================================
echo   SUPER YOUTUBE AGENT - MULTI-CHANNEL AUTOMATION SUITE
echo =========================================================================
echo   run.bat                  - Render Demo Short (Channel 1: FactShorts)
echo   run.bat --channel1       - Run Channel 1 (FactShorts)
echo   run.bat --channel2       - Run Channel 2 (Story Studio on port 8787)
echo   run.bat --channel3       - Run Channel 3 (Dark Sutra True Crime / Mystery)
echo   run.bat --sutra          - Alias for Dark Sutra
echo   run.bat --channel4       - Run Channel 4 (Lofi 24/7 Studio)
echo   run.bat --channel5       - Run Channel 5 (The Global Ledger Map Explainer)
echo   run.bat --ledger         - Alias for The Global Ledger
echo   run.bat --clipper        - Run AI Clipper Best
echo   run.bat --help           - Show this help menu
echo =========================================================================
goto end

:end
