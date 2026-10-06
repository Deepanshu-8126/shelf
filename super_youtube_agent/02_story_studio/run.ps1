param (
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)
$parentRun = Join-Path (Split-Path -Parent $PSScriptRoot) "run.ps1"
if (Test-Path $parentRun) {
    & $parentRun @ArgsList
} else {
    python server.py
}
