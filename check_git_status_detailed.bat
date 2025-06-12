@echo off
cd /d "c:\Users\user\Documents\GitHub\golf_score"
echo === Current Branch ===
git branch
echo.
echo === Remote Branches ===
git branch -r
echo.
echo === Git Status ===
git status
echo.
echo === Latest Commits ===
git log --oneline -5
echo.
echo === Remote Status ===
git remote -v
echo.
echo === Push Status ===
git log origin/develop..develop --oneline
echo.
pause
