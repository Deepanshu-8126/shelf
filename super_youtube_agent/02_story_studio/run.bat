@echo off
if exist "..\run.bat" (
    call "..\run.bat" %*
) else (
    python server.py
)
