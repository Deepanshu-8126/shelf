param (
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptDir\factshorts-bot"

$pythonExe = "$scriptDir\factshorts-bot\venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "Virtual environment not found at $pythonExe" -ForegroundColor Red
    exit 1
}

if ($ArgsList.Count -eq 0) {
    Write-Host "[FactShorts Bot] Running demo render..." -ForegroundColor Cyan
    & $pythonExe main.py --demo
} else {
    & $pythonExe main.py @ArgsList
}
