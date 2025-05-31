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
    summary = []
    for line in changed:
        status, path = line[:2].strip(), line[3:].strip()
        if status == 'A':
            summary.append(f"add: {path}")
        elif status == 'M':
            summary.append(f"fix: {path}")
        elif status == 'D':
            summary.append(f"remove: {path}")
        else:
            summary.append(f"update: {path}")
    msg = ", ".join(summary)
    # 日付を付与
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"{msg} ({now})"

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
