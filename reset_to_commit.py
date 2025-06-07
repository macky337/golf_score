#!/usr/bin/env python3
import subprocess
import os
import sys

def run_git_command(command):
    """Gitコマンドを実行してリザルトを返す"""
    try:
        result = subprocess.run(
            command,
            cwd=r"c:\Users\user\Documents\GitHub\golf_score",
            capture_output=True,
            text=True,
            shell=True
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("=== Git Status Check ===")
    
    # 現在の状態を確認
    stdout, stderr, code = run_git_command("git status --short")
    print(f"Git status:")
    print(stdout if stdout else "No changes")
    if stderr:
        print(f"Error: {stderr}")
    
    # コミット履歴確認
    stdout, stderr, code = run_git_command("git log --oneline -10")
    print(f"\nRecent commits:")
    print(stdout)
    
    # 指定されたコミットが存在するか確認
    target_commit = "e53d2ddc54bdb1a3533294f5c73e2203525fe938"
    stdout, stderr, code = run_git_command(f"git show --stat {target_commit}")
    print(f"\nTarget commit {target_commit}:")
    if code == 0:
        print("✅ Commit exists")
        print(stdout[:500] + "..." if len(stdout) > 500 else stdout)
    else:
        print("❌ Commit not found")
        print(stderr)
    
    # リセット実行可能性の確認
    print(f"\n=== Reset to {target_commit} ===")
    if code == 0:
        confirm = input("Reset to this commit? (y/N): ")
        if confirm.lower() == 'y':
            stdout, stderr, code = run_git_command(f"git reset --hard {target_commit}")
            if code == 0:
                print("✅ Reset successful")
                print(stdout)
                
                # リモートとの同期確認
                stdout, stderr, code = run_git_command("git status")
                print("\nCurrent status after reset:")
                print(stdout)
            else:
                print("❌ Reset failed")
                print(stderr)
        else:
            print("Reset cancelled")
    else:
        print("Cannot reset - commit not found")

if __name__ == "__main__":
    main()
