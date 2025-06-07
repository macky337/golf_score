#!/usr/bin/env python3
"""
重複しているページファイルを削除するスクリプト
"""
import os
import sys

def remove_duplicate_pages():
    """重複ページファイルを削除"""
    pages_dir = os.path.join(os.path.dirname(__file__), "pages")
    
    # 削除対象ファイル
    duplicate_files = [
        "06_結果確認.py",  # 05_結果確認.pyが正しい
        "07_ポイント集計.py",  # 06_ポイント集計.pyが正しい
    ]
    
    for file_name in duplicate_files:
        file_path = os.path.join(pages_dir, file_name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ 削除完了: {file_name}")
            except Exception as e:
                print(f"❌ 削除失敗: {file_name} - {e}")
        else:
            print(f"⚠️  ファイルが見つかりません: {file_name}")

if __name__ == "__main__":
    print("重複ページファイルの削除を開始...")
    remove_duplicate_pages()
    print("削除処理完了")
