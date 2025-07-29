@echo off
REM This batch file stages, commits, and pushes changes to your GitHub repository.
REM It operates on the current working directory and prompts for a commit message.

REM Stage all changes
echo Staging changes...
git add .

REM Check if there are any changes to commit
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo No changes to commit.
    goto :eof
)

REM Prompt for commit message
set /p commit_message="Enter commit message: "

IF "%commit_message%"=="" (
    echo Error: No commit message provided. Aborting.
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