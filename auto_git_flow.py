import subprocess
import datetime
import os

def run_git_command(cmd, cwd=None):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        raise Exception(f"Command failed: {' '.join(cmd)}")

# 変更ファイル一覧を取得し、コミットメッセージを自動生成

def generate_commit_message():
    result = subprocess.run(["git", "status", "-s"], capture_output=True, text=True)
    changed = result.stdout.strip().splitlines()
    if not changed:
        return "chore: no changes"
    
    # ファイルの種類別にカウント
    added_files = []
    modified_files = []
    deleted_files = []
    renamed_files = []
    
    for line in changed:
        status = line[:2].strip()
        path = line[3:].strip()
        filename = os.path.basename(path)
        
        if status == 'A':
            added_files.append(filename)
        elif status == 'M':
            modified_files.append(filename)
        elif status == 'D':
            deleted_files.append(filename)
        elif status in ['R', 'RM']:
            renamed_files.append(filename)
        else:
            modified_files.append(filename)
    
    # メッセージの構築
    parts = []
    
    if added_files:
        if len(added_files) == 1:
            parts.append(f"feat: add {added_files[0]}")
        else:
            parts.append(f"feat: add {len(added_files)} files")
    
    if modified_files:
        # ファイル名から推測される変更内容
        if any('fix' in f.lower() or 'bug' in f.lower() for f in modified_files):
            action = "fix"
        elif any('test' in f.lower() for f in modified_files):
            action = "test"
        elif any('config' in f.lower() or 'setting' in f.lower() for f in modified_files):
            action = "config"
        elif any('.py' in f for f in modified_files):
            action = "update"
        else:
            action = "chore"
        
        if len(modified_files) == 1:
            parts.append(f"{action}: update {modified_files[0]}")
        else:
            # 主要なファイルタイプを特定
            py_files = [f for f in modified_files if f.endswith('.py')]
            if py_files and len(py_files) == len(modified_files):
                parts.append(f"{action}: update {len(py_files)} Python files")
            else:
                parts.append(f"{action}: update {len(modified_files)} files")
    
    if deleted_files:
        if len(deleted_files) == 1:
            parts.append(f"remove: delete {deleted_files[0]}")
        else:
            parts.append(f"remove: delete {len(deleted_files)} files")
    
    if renamed_files:
        if len(renamed_files) == 1:
            parts.append(f"refactor: rename {renamed_files[0]}")
        else:
            parts.append(f"refactor: rename {len(renamed_files)} files")
    
    # メッセージを結合（最初の項目のみ使用してシンプルに）
    if parts:
        main_msg = parts[0]
        if len(parts) > 1:
            main_msg += f" and {len(parts)-1} more changes"
    else:
        main_msg = "chore: update files"
    
    # 日付を付与
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"{main_msg} ({now})"

def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    # 1. git add .
    run_git_command(["git", "add", "."], cwd=repo_dir)
    # 2. git commit -m "..."
    commit_msg = generate_commit_message()
    run_git_command(["git", "commit", "-m", commit_msg], cwd=repo_dir)
    # 3. git push
    run_git_command(["git", "push"], cwd=repo_dir)
    # 4. git checkout main
    run_git_command(["git", "checkout", "main"], cwd=repo_dir)
    # 5. git pull origin main
    run_git_command(["git", "pull", "origin", "main"], cwd=repo_dir)
    # 6. git merge develop
    run_git_command(["git", "merge", "develop"], cwd=repo_dir)
    # 7. git push origin main
    run_git_command(["git", "push", "origin", "main"], cwd=repo_dir)
    # 8. git checkout develop
    run_git_command(["git", "checkout", "develop"], cwd=repo_dir)
    print("\n=== Git flow 完了 ===")

if __name__ == "__main__":
    main()
