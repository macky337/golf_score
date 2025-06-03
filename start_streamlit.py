#!/usr/bin/env python3
"""
Streamlitアプリ起動スクリプト
"""
import subprocess
import sys
import os

def start_streamlit():
    """Streamlitアプリを起動"""
    # プロジェクトルートディレクトリに移動
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    print(f"現在のディレクトリ: {os.getcwd()}")
    print("Streamlitアプリを起動中...")
    
    try:
        # Streamlitコマンドを実行
        cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"]
        print(f"実行コマンド: {' '.join(cmd)}")
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 出力をリアルタイムで表示
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # エラー出力があれば表示
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"エラー出力: {stderr_output}")
            
    except Exception as e:
        print(f"Streamlit起動エラー: {e}")

if __name__ == "__main__":
    start_streamlit()
