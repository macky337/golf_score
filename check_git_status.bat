@echo off
cd /d "c:\Users\user\Documents\GitHub\golf_score"
echo === Current Git Status ===
git status --short
echo.
echo === Recent Commits ===
git log --oneline -10
echo.
echo === Checking target commit ===
git show --stat e53d2ddc54bdb1a3533294f5c73e2203525fe938
pause
