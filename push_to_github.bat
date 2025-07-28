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

REM Use the first argument as the commit message
set "commit_message=%~1"

IF "%commit_message%"=="" (
    echo Error: No commit message provided.
    exit /b 1
)

REM Commit the changes
echo Committing changes...
git commit -m "%commit_message%"

REM Push the changes to GitHub
echo Pushing changes to GitHub...
git push origin master

echo Done.
pause