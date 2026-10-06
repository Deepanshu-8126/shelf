@echo off
cd /d "%~dp0"
if exist ".\venv\Scripts\activate.bat" call ".\venv\Scripts\activate.bat"

if "%~1"=="" (
    echo [FactShorts Bot] Running demo video render...
    python main.py --demo
) else (
    python main.py %*
)
