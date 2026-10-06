param (
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptDir"

$pythonExe = "$scriptDir\venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

if ($ArgsList.Count -eq 0) {
    Write-Host "[FactShorts Bot] Running demo render..." -ForegroundColor Cyan
    & $pythonExe main.py --demo
} else {
    & $pythonExe main.py @ArgsList
}
