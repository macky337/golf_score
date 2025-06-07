import subprocess
import os
import sys

def run_command(cmd, cwd=None):
    print(f"実行: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding='cp932')
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.stdout, result.stderr, result.returncode == 0
    except Exception as e:
        print(f"コマンド実行エラー: {e}")
        return "", str(e), False

def check_git_status():
    stdout, stderr, success = run_command(["git", "status"])
    
    if "detached HEAD" in stdout or "detached HEAD" in stderr:
        print("警告: detached HEAD状態が検出されました")
        return "detached"
        
    if "On branch" in stdout:
        branch = stdout.split("On branch")[1].split("\n")[0].strip()
        print(f"現在のブランチ: {branch}")
        return branch
    
    return None

def check_available_branches():
    stdout, stderr, success = run_command(["git", "branch"])
    if success:
        branches = [b.strip().replace("* ", "") for b in stdout.splitlines() if b.strip()]
        print(f"利用可能なブランチ: {', '.join(branches)}")
        return branches
    return []

def fix_detached_head():
    print("\n===== Git状態修復 =====")
    
    # 1. 変更を一時保存
    stdout, stderr, success = run_command(["git", "stash"])
    if not success:
        print("変更の一時保存に失敗しました。手動で対応してください。")
        return False
    
    # 2. 利用可能なブランチを確認
    branches = check_available_branches()
    
    target_branch = None
    if "develop" in branches:
        target_branch = "develop"
    elif "main" in branches or "master" in branches:
        target_branch = "main" if "main" in branches else "master"
    
    if not target_branch:
        print("適切なブランチが見つかりません。手動で対応してください。")
        return False
    
    # 3. ブランチに切り替え
    print(f"\n{target_branch}ブランチに切り替えます...")
    stdout, stderr, success = run_command(["git", "checkout", target_branch])
    if not success:
        print(f"{target_branch}ブランチへの切り替えに失敗しました。手動で対応してください。")
        return False
    
    # 4. 一時保存した変更を適用
    stdout, stderr, success = run_command(["git", "stash", "pop"])
    
    # 5. 状態を再確認
    status = check_git_status()
    if status == "detached":
        print("修復に失敗しました。手動で対応してください。")
        return False
    
    print(f"正常に{status}ブランチに復帰しました！")
    return True

def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(repo_dir)
    
    print("===== Git状態診断 =====")
    status = check_git_status()
    
    if status == "detached":
        print("detached HEAD状態を修復します...")
        if fix_detached_head():
            print("\n修復が完了しました。auto_git_flow.pyを再度実行してください。")
        else:
            print("\n自動修復に失敗しました。以下の手順で手動修復を行ってください:")
            print("1. git branch    # 利用可能なブランチを確認")
            print("2. git checkout develop  # developブランチに切り替え")
            print("3. python auto_git_flow.py  # 再度スクリプトを実行")
    elif status:
        print(f"Gitの状態は正常です。ブランチ: {status}")
    else:
        print("Gitの状態を判断できませんでした。手動で確認してください。")

if __name__ == "__main__":
    main()
