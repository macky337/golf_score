import subprocess
import os

def execute_git_reset():
    """指定されたコミットにリセット"""
    target_commit = "e53d2ddc54bdb1a3533294f5c73e2203525fe938"
    repo_path = r"c:\Users\user\Documents\GitHub\golf_score"
    
    print(f"Resetting to commit: {target_commit}")
    
    try:
        # 作業ディレクトリを変更
        os.chdir(repo_path)
        
        # Git reset --hard を実行
        result = subprocess.run(
            ["git", "reset", "--hard", target_commit],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("✅ Reset successful!")
        print(f"Output: {result.stdout}")
        
        # 状態確認
        status_result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True
        )
        
        print("\nCurrent status:")
        print(status_result.stdout if status_result.stdout else "Working tree clean")
        
        # ログ確認
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True,
            text=True
        )
        
        print("\nRecent commits:")
        print(log_result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git command failed: {e}")
        print(f"Error output: {e.stderr}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    execute_git_reset()
