@echo off
set SCRIPT_DIR=%~dp0
call "%SCRIPT_DIR%factshorts-bot\venv\Scripts\activate.bat"

if /i "%~1"=="--studio" goto studio
if /i "%~1"=="--gaming" goto studio

cd /d "%SCRIPT_DIR%factshorts-bot"
if "%~1"=="" (
    echo [FactShorts Bot] Running demo video render...
    python main.py --demo
) else (
    python main.py %*
)
goto end

:studio
cd /d "%SCRIPT_DIR%youtube_agent_studio"
echo [CreatorOps / YouTube Agent Studio] Starting Web Server at http://localhost:8787...
echo Features: GTA VI Clips Lab (Hindi/Hinglish) + Market Scout + Documentary Research + Strategy Calendar
python server.py

:end

