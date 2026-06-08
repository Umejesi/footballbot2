@echo off
echo ============================================
echo  FootballAI Bot - Auto Setup
echo ============================================
echo.

REM Check if Python 3.11 is available via py launcher
py -3.11 --version >nul 2>&1
if %errorlevel% == 0 (
    echo Found Python 3.11 - Good!
    goto install
)

echo Python 3.11 not found. Downloading now...
echo This will take about 2 minutes...
echo.

REM Download Python 3.11 installer
curl -o python311.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

echo Installing Python 3.11...
python311.exe /quiet InstallAllUsers=0 PrependPath=0 Include_pip=1

del python311.exe
echo Python 3.11 installed!

:install
echo.
echo Installing bot requirements...
py -3.11 -m pip install python-telegram-bot==20.7 httpx==0.25.2 sqlalchemy python-dotenv aiohttp apscheduler

echo.
echo ============================================
echo  All done! Now run: start_bot.bat
echo ============================================
pause
