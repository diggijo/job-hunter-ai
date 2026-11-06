# Job Hunter AI - Check Retry Queue
# Read-only: No Gemini API requests

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path

Push-Location $ProjectRoot

try {
    Write-Host ""
    Write-Host "=== Job Hunter AI - Retry Queue ===" -ForegroundColor Cyan

    python -c "from app.database import get_ai_evaluation_queue; jobs = get_ai_evaluation_queue(candidate_id=1); print(f'Jobs waiting: {len(jobs)}'); print('-' * 90); [print('{} | {} | {}'.format(j['job_id'], j['company'], j['title'])) for j in jobs]"

    Write-Host ""
}
finally {
    Pop-Location
}
