
@echo off
cd /d "C:\Users\josep\AI\job-hunter-ai"

if not exist "logs" mkdir "logs"

echo. >> "logs\daily_ai.log"
echo ===== Daily job collection started: %date% %time% ===== >> "logs\daily_ai.log"

".venv\Scripts\python.exe" -m app.run_full_collection >> "logs\daily_ai.log" 2>&1

if errorlevel 1 (
    echo Greenhouse or Ashby collection failed. Skipping Gemini. >> "logs\daily_ai.log"
    exit /b 1
)

echo ===== Greenhouse and Ashby collection completed: %date% %time% ===== >> "logs\daily_ai.log"
echo ===== Gemini evaluation started ===== >> "logs\daily_ai.log"

".venv\Scripts\python.exe" -m app.run_daily_ai >> "logs\daily_ai.log" 2>&1

if errorlevel 1 exit /b 1

echo ===== Daily process completed: %date% %time% ===== >> "logs\daily_ai.log"
