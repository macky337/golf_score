@echo off
cd /d "c:\Users\user\Documents\GitHub\golf_score"
echo Executing git reset --hard to e53d2ddc54bdb1a3533294f5c73e2203525fe938
git reset --hard e53d2ddc54bdb1a3533294f5c73e2203525fe938
echo Reset completed. Current status:
git status
echo.
echo Recent commits:
git log --oneline -5
pause
