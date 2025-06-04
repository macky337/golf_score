#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHANGELOGファイル読み込みテストスクリプト
"""

import os
import sys

def test_changelog_loading():
    """CHANGELOGファイルの読み込みテスト"""
    print("=== CHANGELOGファイル読み込みテスト ===")
    
    # 現在のディレクトリ情報
    current_dir = os.getcwd()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"現在のディレクトリ: {current_dir}")
    print(f"スクリプトのディレクトリ: {script_dir}")
    
    # 相対パスでのテスト
    relative_path = "CHANGELOG.md"
    print(f"\n--- 相対パステスト ---")
    print(f"パス: {relative_path}")
    print(f"存在確認: {os.path.exists(relative_path)}")
    
    # 絶対パスでのテスト
    absolute_path = os.path.join(script_dir, "CHANGELOG.md")
    print(f"\n--- 絶対パステスト ---")
    print(f"パス: {absolute_path}")
    print(f"存在確認: {os.path.exists(absolute_path)}")
    
    # ファイル読み込みテスト
    try:
        if os.path.exists(absolute_path):
            with open(absolute_path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"\n--- 読み込み成功 ---")
            print(f"ファイルサイズ: {len(content)} 文字")
            print(f"最初の100文字: {content[:100]}")
        else:
            print("\n--- エラー ---")
            print("CHANGELOGファイルが見つかりません")
    except Exception as e:
        print(f"\n--- 読み込みエラー ---")
        print(f"エラー: {str(e)}")
    
    # ディレクトリ内容確認
    print(f"\n--- ディレクトリ内容 ---")
    try:
        files = [f for f in os.listdir(script_dir) if f.endswith('.md')]
        print(f"MDファイル: {files}")
    except Exception as e:
        print(f"ディレクトリ読み込みエラー: {str(e)}")

if __name__ == "__main__":
    test_changelog_loading()
