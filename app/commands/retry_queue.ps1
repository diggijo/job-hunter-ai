# Job Hunter AI - Run Retry Queue
# Makes Gemini API requests

param(
    [int]$MaxCalls = 100
)

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path

Push-Location $ProjectRoot

try {
    Write-Host ""
    Write-Host "=== Job Hunter AI - Retry Queue ===" -ForegroundColor Cyan

    if ($MaxCalls -le 0) {
        Write-Host "MaxCalls must be greater than zero." -ForegroundColor Red
        return
    }

    python -c "from app.database import get_ai_evaluation_queue; print('Jobs waiting:', len(get_ai_evaluation_queue(candidate_id=1)))"

    Write-Host ""
    Write-Host "Maximum Gemini requests: $MaxCalls" -ForegroundColor Yellow

    $Confirmation = Read-Host "Start retrying? (Y/N)"

    if ($Confirmation -ne "Y") {
        Write-Host "Cancelled. No Gemini requests made."
        return
    }

    python -c "from app.retry_ai_queue import run_locked_retry; run_locked_retry(candidate_id=1, max_api_calls=$MaxCalls)"

    Write-Host ""
    Write-Host "=== Remaining Queue ===" -ForegroundColor Cyan

    python -c "from app.database import get_ai_evaluation_queue; print('Jobs remaining:', len(get_ai_evaluation_queue(candidate_id=1)))"
}
finally {
    Pop-Location
}