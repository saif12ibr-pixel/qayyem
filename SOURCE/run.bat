@echo off
rem ---------------------------------------------------------------------------
rem  Qayyem - one-click launcher for Windows.
rem  Creates the virtual environment, installs dependencies, prepares the
rem  database, then starts the server and opens it in the browser.
rem  Safe to run repeatedly: each step is skipped if it is already done, and an
rem  existing database is upgraded to the current version when the app starts.
rem ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0"
set "URL=http://127.0.0.1:5000"
set "OPEN=%URL%"

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

rem Run on every start, so updates that add a library (such as pypdf for
rem reading books and slides) are installed without a manual step.
echo  [2/4] Installing dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if errorlevel 1 goto :failed

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo  [3/4] Created .env from .env.example.
  echo.
  echo      An AI key is needed to grade. Either paste a server-wide key into
  echo      .env ^(GEMINI_API_KEY, free at https://aistudio.google.com/apikey^),
  echo      or let each instructor add their own under Settings in the app.
  echo.
) else (
  echo  [3/4] Configuration file .env found.
)

rem Whether instructors can create their own account (SIGNUP_ENABLED in .env).
python -c "import sys; from config import Config; sys.exit(0 if Config.SIGNUP_ENABLED else 1)" >nul 2>nul
if errorlevel 1 (set "SIGNUP=0") else (set "SIGNUP=1")

if not exist "instance\qayyem.sqlite3" (
  echo  [4/4] Preparing the database...
  flask --app app init-db
  if errorlevel 1 goto :failed
  if "%SIGNUP%"=="0" (
    echo.
    echo  Sign-up is turned off in .env, so create the first instructor login here:
    echo.
    flask --app app create-instructor
    if errorlevel 1 goto :failed
  ) else (
    echo.
    echo  Create your instructor account in the browser: %URL%/signup
    set "OPEN=%URL%/signup"
  )
) else (
  echo  [4/4] Database found. It is upgraded to the latest version on start,
  echo        keeping every account, subject and question bank.
)

echo.
echo  Starting Qayyem at %URL%
echo  Subjects, question banks from Word, sign-up and reviewing grades are in
echo  the menu at the top of the page. Press Ctrl+C here to stop the server.
echo.

rem Open the browser once the server has had a moment to start. ping is the
rem delay because timeout refuses to run when input is redirected.
start "" /b cmd /c "ping -n 4 127.0.0.1 >nul & start "" "%OPEN%""
flask --app app run
goto :eof

:failed
echo.
echo  [X] A step failed. Read the message above.
echo.
pause
exit /b 1
