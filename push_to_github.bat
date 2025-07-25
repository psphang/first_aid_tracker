@echo off
REM This batch file stages, commits, and pushes changes to your GitHub repository.

REM Navigate to the repository directory
cd /d "%~dp0"

REM Stage all changes
echo Staging changes...
git add .

REM Check if there are any changes to commit
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo No changes to commit.
    goto :eof
)

REM Prompt for a commit message
set /p commit_message="Enter your commit message: "

REM Commit the changes
echo Committing changes...
git commit -m "%commit_message%"

REM Push the changes to GitHub
echo Pushing changes to GitHub...
git push origin master

echo Done.
pause