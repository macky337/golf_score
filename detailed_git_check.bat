@echo off
chcp 65001
cd /d "c:\Users\user\Documents\GitHub\golf_score"

echo === Current Branch ===
git rev-parse --abbrev-ref HEAD

echo.
echo === Working Directory Status ===
git status --short

echo.
echo === Staged Changes ===
git diff --cached --name-only

echo.
echo === Latest Local Commits ===
git log --oneline -5

echo.
echo === Remote Tracking ===
git log --oneline origin/develop -3

echo.
echo === Comparison with Remote ===
git log origin/develop..HEAD --oneline

echo.
echo === Remote URLs ===
git remote -v

pause
