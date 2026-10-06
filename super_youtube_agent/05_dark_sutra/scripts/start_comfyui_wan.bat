@echo off
setlocal enabledelayedexpansion
title ComfyUI + Wan 2.2 Local GPU Server (Channel 5: Dark Sutra)
color 0C

echo ================================================================
echo    🎬 COMFYUI + WAN 2.2 LOCAL GPU SERVER (DARK SUTRA STUDIO)
echo ================================================================
echo   License : Wan 2.2 (Apache 2.0 - 100%% Free, No Watermark)
echo   Hardware: NVIDIA GPU (12GB - 24GB VRAM Recommended)
echo   Endpoint: http://127.0.0.1:8188
echo ================================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "STUDIO_DIR=%SCRIPT_DIR%.."
set "COMFY_DIR=%STUDIO_DIR%\ComfyUI"

:: 1. Check if ComfyUI is already cloned
if not exist "%COMFY_DIR%" (
    echo [Step 1/4] Cloning ComfyUI repository...
    git clone https://github.com/comfyanonymous/ComfyUI "%COMFY_DIR%"
    if errorlevel 1 (
        echo [ERROR] Git clone failed. Please make sure Git is installed and internet is connected.
        pause
        exit /b 1
    )
) else (
    echo [Step 1/4] ComfyUI already cloned in %COMFY_DIR%.
)

cd /d "%COMFY_DIR%"

:: 2. Setup Python virtual environment
if not exist "venv" (
    echo.
    echo [Step 2/4] Setting up Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Make sure Python 3.10/3.11 is installed.
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo Upgrading pip and installing PyTorch with CUDA 12.1...
    python -m pip install --upgrade pip
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    pip install -r requirements.txt
) else (
    echo [Step 2/4] Virtual environment exists. Activating...
    call venv\Scripts\activate.bat
)

:: 3. Check Wan 2.2 Models
set "MODELS_DIR=%COMFY_DIR%\models\diffusion_models"
if not exist "%MODELS_DIR%" mkdir "%MODELS_DIR%"

echo.
echo [Step 3/4] Checking Wan 2.2 Model in %MODELS_DIR%...
dir "%MODELS_DIR%\*wan*" >nul 2>&1
if errorlevel 1 (
    echo ----------------------------------------------------------------
    echo ℹ️  Wan 2.2 Model not detected in %MODELS_DIR%.
    echo    To download Wan 2.2 Text-to-Video Model:
    echo    Option A (Fast 1.3B, 8-12GB VRAM):
    echo      pip install huggingface_hub
    echo      huggingface-cli download Wan-AI/Wan2.1-T2V-1.3B --local-dir "%MODELS_DIR%\Wan2.1-1.3B"
    echo    Option B (Full 14B Cinema, 16-24GB VRAM):
    echo      huggingface-cli download Wan-AI/Wan2.1-T2V-14B --local-dir "%MODELS_DIR%\Wan2.1-14B"
    echo.
    echo    You can still run ComfyUI now and install models via ComfyUI Manager!
    echo ----------------------------------------------------------------
) else (
    echo ✅ Wan model files found in models directory!
)

:: 4. Start Server
echo.
echo [Step 4/4] Launching ComfyUI on http://127.0.0.1:8188 ...
echo Press Ctrl+C in this terminal window to stop the server.
echo.
python main.py --listen 127.0.0.1 --port 8188 --preview-method auto

pause
