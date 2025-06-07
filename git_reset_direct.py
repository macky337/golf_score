import os
import subprocess
import sys

# ディレクトリ変更
os.chdir(r"c:\Users\user\Documents\GitHub\golf_score")

print("Current directory:", os.getcwd())
print("Executing git reset --hard e53d2ddc54bdb1a3533294f5c73e2203525fe938...")

try:
    # Git reset --hard を実行
    result = subprocess.run(
        ["git", "reset", "--hard", "e53d2ddc54bdb1a3533294f5c73e2203525fe938"],
        capture_output=True,
        text=True,
        shell=True
    )
    
    print("Git reset result:")
    print("Return code:", result.returncode)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    # 現在の状態を確認
    status_result = subprocess.run(
        ["git", "status"],
        capture_output=True,
        text=True,
        shell=True
    )
    
    print("\nCurrent git status:")
    print(status_result.stdout)
    
except Exception as e:
    print(f"Error: {e}")

print("\nScript completed.")
