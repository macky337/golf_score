#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高速デプロイ用のGitワークフロー
最適化 → コミット → プッシュを自動実行
"""

import subprocess
import datetime
import os
import sys

def run_command(cmd, cwd=None):
    """コマンド実行"""
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if result.returncode != 0:
        raise Exception(f"Command failed: {' '.join(cmd)}")
    return result

def optimize_for_deploy():
    """デプロイ用最適化"""
    print("🚀 デプロイ最適化を実行...")
    try:
        run_command([sys.executable, "optimize_for_deploy.py"])
        return True
    except Exception as e:
        print(f"❌ 最適化に失敗: {e}")
        return False

def check_git_status():
    """Git状況確認"""
    result = run_command(["git", "status", "--porcelain"])
    return result.stdout.strip()

def fast_deploy():
    """高速デプロイ実行"""
    
    print("⚡ 高速デプロイワークフローを開始...\n")
    
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. デプロイ用最適化
    if not optimize_for_deploy():
        print("❌ 最適化に失敗したため、デプロイを中断します")
        return
    
    print()
    
    # 2. 変更確認
    print("📋 変更ファイルを確認...")
    changes = check_git_status()
    if not changes:
        print("📝 変更がありません。デプロイをスキップします。")
        return
    
    print(f"📝 {len(changes.splitlines())}個の変更ファイルが見つかりました")
    
    # 3. ステージング
    print("\n📦 ファイルをステージング...")
    run_command(["git", "add", "."], cwd=repo_dir)
    
    # 4. コミット
    print("\n💾 変更をコミット...")
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    commit_msg = f"🚀 デプロイ用最適化 ({now})"
    run_command(["git", "commit", "-m", commit_msg], cwd=repo_dir)
    
    # 5. プッシュ（現在のブランチに）
    print("\n⬆️ 変更をプッシュ...")
    try:
        # 現在のブランチを取得
        result = run_command(["git", "branch", "--show-current"], cwd=repo_dir)
        current_branch = result.stdout.strip()
        
        if current_branch:
            run_command(["git", "push", "origin", current_branch], cwd=repo_dir)
        else:
            run_command(["git", "push"], cwd=repo_dir)
            
    except Exception as e:
        print(f"⚠️ プッシュに失敗: {e}")
        print("📝 手動でプッシュしてください: git push")
        return
    
    print("\n✅ === 高速デプロイ完了！ ===")
    print("🎉 最適化されたコードがリポジトリにプッシュされました")
    print("⚡ デプロイ時間が大幅に短縮されるはずです")

if __name__ == "__main__":
    fast_deploy()
