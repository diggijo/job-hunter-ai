
# Job Hunter AI - Manage Preferences
# View, add, and remove preferred locations
# No Gemini API requests
# .\app\commands\manage_preferences.ps1 

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path

Push-Location $ProjectRoot

try {
    Write-Host ""
    Write-Host "=== Job Hunter AI - Manage Preferences ===" -ForegroundColor Cyan

    python -m app.manage_preferences

    Write-Host ""
}
finally {
    Pop-Location
}
