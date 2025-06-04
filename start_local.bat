@echo off
echo ゴルフスコアアプリを起動中...
echo URL: http://localhost:8503
streamlit run main.py --server.port 8503 --server.address 127.0.0.1
pause
