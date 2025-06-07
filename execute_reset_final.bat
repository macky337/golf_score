@echo off
cd /d "c:\Users\user\Documents\GitHub\golf_score"
echo Current directory: %CD%
echo.
echo Checking git status...
git status --porcelain
echo.
echo Executing git reset --hard e53d2ddc54bdb1a3533294f5c73e2203525fe938
git reset --hard e53d2ddc54bdb1a3533294f5c73e2203525fe938
echo.
echo Verifying reset...
git log --oneline -1
echo.
echo Final status check...
git status --porcelain
echo.
echo Reset completed!
pause
