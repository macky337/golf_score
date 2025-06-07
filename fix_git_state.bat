@echo off
cd /d "%~dp0"
echo Git状態修復を開始します...
python fix_git_state.py
echo.
echo 処理が完了しました。
pause
