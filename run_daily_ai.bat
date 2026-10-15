@echo off
cd /d "C:\Users\josep\AI\job-hunter-ai"
if not exist "logs" mkdir "logs"
".venv\Scripts\python.exe" -m app.run_daily_ai >> "logs\daily_ai.log" 2>&1
