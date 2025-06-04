#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デプロイ前の最適化処理
不要ファイルの削除、依存関係の最適化など
"""

import os
import shutil
import subprocess
import glob

def clean_unnecessary_files():
    """不要なファイルを削除してデプロイサイズを削減"""
    
    print("🧹 不要ファイルのクリーンアップを開始...")
    
    # 削除対象のパターン
    patterns_to_delete = [
        "test_*.py",
        "*_test.py", 
        "debug_*.py",
        "analyze_*.py",
        "check_*.py",
        "diagnose_*.py",
        "investigate_*.py",
        "fix_*.py",
        "clean_*.py",
        "create_*_folder.py",
        "migrate_*.py",
        "restore_*.py",
        "add_*.py",
        "simple_*.py",
        "dummy_*.py",
        "manual_test.py",
        "*.db",
        "*.sqlite",
        "dump.sql",
        "output.txt",
        "nul"
    ]
    
    deleted_count = 0
    for pattern in patterns_to_delete:
        files = glob.glob(pattern)
        for file in files:
            if os.path.exists(file) and file != "auto_git_flow.py":  # 除外
                try:
                    os.remove(file)
                    print(f"  ✅ 削除: {file}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  ❌ 削除失敗: {file} - {e}")
    
    # ディレクトリの削除
    dirs_to_delete = [
        "__pycache__",
        ".pytest_cache", 
        "tests",
        "backup",
        "temp"
    ]
    
    for dir_name in dirs_to_delete:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"  ✅ ディレクトリ削除: {dir_name}")
                deleted_count += 1
            except Exception as e:
                print(f"  ❌ ディレクトリ削除失敗: {dir_name} - {e}")
    
    print(f"🎉 クリーンアップ完了！ {deleted_count}個のファイル/ディレクトリを削除")

def optimize_requirements():
    """requirements.txtを本番用に最適化"""
    
    print("📦 依存関係の最適化...")
    
    # requirements-minimal.txtがあればそれを使用
    if os.path.exists("requirements-minimal.txt"):
        shutil.copy("requirements-minimal.txt", "requirements.txt")
        print("  ✅ 軽量版requirements.txtに切り替え")
    else:
        print("  ⚠️ requirements-minimal.txtが見つかりません")

def check_main_file():
    """メインファイルの存在確認"""
    
    print("🔍 メインファイルの確認...")
    
    if os.path.exists("main_fixed.py"):
        print("  ✅ main_fixed.py が見つかりました")
    elif os.path.exists("main.py"):
        print("  ✅ main.py が見つかりました")
    else:
        print("  ❌ メインファイルが見つかりません！")
        return False
    
    return True

def main():
    """メイン処理"""
    
    print("🚀 デプロイ最適化を開始します...\n")
    
    # メインファイルの確認
    if not check_main_file():
        print("❌ 最適化を中断します")
        return
    
    print()
    
    # 不要ファイルの削除
    clean_unnecessary_files()
    
    print()
    
    # 依存関係の最適化
    optimize_requirements()
    
    print()
    print("✨ デプロイ最適化が完了しました！")
    print("📈 これでデプロイ時間が大幅に短縮されるはずです")

if __name__ == "__main__":
    main()
