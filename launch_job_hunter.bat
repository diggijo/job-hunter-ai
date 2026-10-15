@echo off
cd /d "C:\Users\josep\AI\job-hunter-ai"

start "Job Hunter AI Server" /min ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

timeout /t 3 /nobreak >nul

start "" "http://127.0.0.1:8000/"

exit