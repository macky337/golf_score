@echo off
cd /d "%~dp0"
echo Git自動化処理を開始します...
python auto_git_flow.py
echo.
echo 処理が完了しました。
pause
