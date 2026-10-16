@echo off
rem ---------------------------------------------------------------------------
rem  Qayyem - one-click launcher for Windows.
rem  Creates the virtual environment, installs dependencies, initialises the
rem  database and the first instructor account, then starts the server.
rem  Safe to run repeatedly: each step is skipped if it is already done.
rem ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0"

echo.
echo  Qayyem - AI-Powered Arabic Assignment Grading
echo  ============================================
echo.

rem The Microsoft Store ships a "python" stub that is on PATH but does not run,
rem so check that Python actually executes rather than just that it exists.
python -c "import sys" >nul 2>nul
if errorlevel 1 (
  echo  [X] Python is not installed, or only the Microsoft Store placeholder is.
  echo.
  echo      Install Python 3.12 from https://www.python.org/downloads/
  echo      During setup, tick "Add python.exe to PATH".
  echo      Then run this file again.
  echo.
  pause
  exit /b 1
)

if not exist ".venv" (
  echo  [1/4] Creating the virtual environment...
  python -m venv .venv
  if errorlevel 1 goto :failed
) else (
  echo  [1/4] Virtual environment already present.
)

call ".venv\Scripts\activate.bat"

echo  [2/4] Installing dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if errorlevel 1 goto :failed

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo.
  echo  [3/4] Created .env
  echo.
  echo      Open .env and paste your free API key into GEMINI_API_KEY.
  echo      Get one at https://aistudio.google.com/apikey
  echo.
  echo      Then run this file again.
  echo.
  pause
  exit /b 0
) else (
  echo  [3/4] Configuration file .env found.
)

if not exist "instance\qayyem.sqlite3" (
  echo  [4/4] Preparing the database...
  flask --app app init-db
  if errorlevel 1 goto :failed
  echo.
  echo  Create your instructor login:
  echo.
  flask --app app create-instructor
  if errorlevel 1 goto :failed
) else (
  echo  [4/4] Database already initialised.
)

echo.
echo  Starting Qayyem at http://127.0.0.1:5000
echo  Press Ctrl+C to stop.
echo.
flask --app app run
goto :eof

:failed
echo.
echo  [X] A step failed. Read the message above.
echo.
pause
exit /b 1
