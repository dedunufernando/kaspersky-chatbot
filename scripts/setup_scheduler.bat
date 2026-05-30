@echo off
echo Setting up daily auto-update for Kaspersky Chatbot...

:: Get Python path
for /f "tokens=*" %%i in ('where python') do set PYTHON_PATH=%%i

:: Set paths
set SCRIPT_PATH=%~dp0..\scripts\daily_update.py
set TASK_NAME=KasperskyChatbotDailyUpdate

:: Delete old task if exists
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: Create new scheduled task — runs daily at midnight
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
  /sc DAILY ^
  /st 00:00 ^
  /ru "%USERNAME%" ^
  /rl HIGHEST ^
  /f

echo.
echo Done! Task "%TASK_NAME%" scheduled to run daily at midnight.
echo To check: schtasks /query /tn "%TASK_NAME%"
echo To run now: schtasks /run /tn "%TASK_NAME%"
echo To remove: schtasks /delete /tn "%TASK_NAME%" /f
pause
