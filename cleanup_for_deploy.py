#!/usr/bin/env python3
"""
デプロイ最適化: 不要なテスト・デバッグファイルの一括削除
"""

import os
import glob

def cleanup_test_files():
    """不要なテスト・デバッグファイルを削除"""
    
    # 削除対象のパターン
    cleanup_patterns = [
        "test_*.py",
        "debug_*.py", 
        "dummy_*.py",
        "temp_*.py",
        "check_*.py",
        "diagnose_*.py",
        "investigate_*.py",
        "fix_*.py",
        "manual_test.py",
        "simple_*.py"
    ]
    
    deleted_files = []
    protected_files = [
        "test_imports.py",  # 既に削除済み
        "modules/test_*.py"  # モジュール内のテストは保持
    ]
    
    for pattern in cleanup_patterns:
        files = glob.glob(pattern)
        for file in files:
            # 重要なファイルは保護
            if any(protected in file for protected in protected_files):
                continue
                
            try:
                os.remove(file)
                deleted_files.append(file)
                print(f"🗑️  削除: {file}")
            except Exception as e:
                print(f"❌ 削除失敗: {file} - {e}")
    
    return deleted_files

if __name__ == "__main__":
    print("🧹 デプロイ最適化: 不要ファイル削除開始")
    deleted = cleanup_test_files()
    print(f"\n✅ 削除完了: {len(deleted)} ファイル")
    print("📦 デプロイサイズ最適化完了")
