param (
    [switch]$Studio,
    [switch]$Gaming,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = "$scriptDir\factshorts-bot\venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "Virtual environment not found at $pythonExe" -ForegroundColor Red
    exit 1
}

if ($Studio -or $Gaming -or ($ArgsList -contains "--studio") -or ($ArgsList -contains "--gaming")) {
    Write-Host "[CreatorOps / YouTube Agent Studio] Starting Web Server at http://localhost:8787..." -ForegroundColor Green
    Write-Host "Features: GTA VI Clips Lab (Hindi/Hinglish) + Market Scout + Documentary Research + Strategy Calendar" -ForegroundColor Cyan
    Set-Location "$scriptDir\youtube_agent_studio"
    & $pythonExe server.py
} elseif ($ArgsList.Count -eq 0) {
    Write-Host "[FactShorts Bot] Running demo render..." -ForegroundColor Cyan
    Set-Location "$scriptDir\factshorts-bot"
    & $pythonExe main.py --demo
} else {
    Set-Location "$scriptDir\factshorts-bot"
    & $pythonExe main.py @ArgsList
}

