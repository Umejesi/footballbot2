@echo off
echo ============================================
echo  FootballAI Bot - GitHub Upload Tool
echo ============================================
echo.
echo This will upload your bot to GitHub automatically.
echo.

REM Ask for GitHub details
set /p GITHUB_USER=Enter your GitHub username: 
set /p GITHUB_REPO=Enter your repo name (e.g. footballbot): 
set /p GITHUB_TOKEN=Enter your GitHub Personal Access Token: 

echo.
echo Setting up Git...

REM Configure git
git config --global user.email "bot@footballai.com"
git config --global user.name "%GITHUB_USER%"

REM Initialize and push
git init
git add .
git commit -m "Add football bot files"
git branch -M main
git remote add origin https://%GITHUB_USER%:%GITHUB_TOKEN%@github.com/%GITHUB_USER%/%GITHUB_REPO%.git
git push -u origin main --force

echo.
echo ============================================
if %errorlevel% == 0 (
    echo  SUCCESS! Files uploaded to GitHub!
    echo  Now go to Railway or Koyeb to deploy.
) else (
    echo  Something went wrong. Check your details.
)
echo ============================================
pause
