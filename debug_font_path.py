#!/usr/bin/env python3
"""フォントファイルのパスを確認するデバッグスクリプト"""

import os
import sys

def check_font_paths():
    """フォントファイルの存在を確認"""
    # 現在のスクリプトの位置を基準に検索パスを生成
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    
    # 検索パス（06_結果確認.pyと同じ構造）
    font_paths = [
        "ipaexg.ttf",  # 現在のディレクトリ
        os.path.join(current_dir, "ipaexg.ttf"),  # スクリプトと同じディレクトリ
        os.path.join(current_dir, "pages", "ipaexg.ttf"),  # pagesディレクトリ内
        os.path.join(current_dir, "deploy_snapshot", "ipaexg.ttf"),  # deploy_snapshotディレクトリ
        os.path.join(os.getcwd(), "ipaexg.ttf"),  # 作業ディレクトリ
        r"c:\Users\user\Documents\GitHub\golf_score\ipaexg.ttf",  # 絶対パス（プロジェクトルート）
        r"c:\Users\user\Documents\GitHub\golf_score\deploy_snapshot\ipaexg.ttf",  # 絶対パス（deploy_snapshot）
        "/app/ipaexg.ttf"  # Railway/Docker環境
    ]
    
    print("=== フォントファイル検索結果 ===")
    print(f"現在のファイル: {current_file}")
    print(f"現在の作業ディレクトリ: {os.getcwd()}")
    print()
    
    found_paths = []
    for i, path in enumerate(font_paths):
        exists = os.path.exists(path)
        status = "✓ 存在する" if exists else "✗ 存在しない"
        print(f"{i+1:2d}. {path}")
        print(f"    {status}")
        if exists:
            found_paths.append(path)
            print(f"    絶対パス: {os.path.abspath(path)}")
        print()
    
    print("=== 見つかったフォントファイル ===")
    if found_paths:
        for path in found_paths:
            print(f"✓ {path}")
            print(f"  絶対パス: {os.path.abspath(path)}")
    else:
        print("フォントファイルが見つかりませんでした。")
    
    return found_paths

if __name__ == "__main__":
    found_paths = check_font_paths()
    
    # 06_結果確認.pyのパスをシミュレート
    print("\n=== 06_結果確認.py からの検索パスシミュレーション ===")
    
    # pagesディレクトリのファイルの場合
    pages_file = r"c:\Users\user\Documents\GitHub\golf_score\pages\06_結果確認.py"
    if os.path.exists(pages_file):
        print(f"Pages版のファイル: {pages_file}")
        pages_dir = os.path.dirname(pages_file)
        pages_paths = [
            os.path.join(pages_dir, "ipaexg.ttf"),  # pagesディレクトリ内
            os.path.join(os.path.dirname(pages_dir), "ipaexg.ttf"),  # プロジェクトルート
        ]
        for path in pages_paths:
            exists = os.path.exists(path)
            print(f"  {path} - {'存在する' if exists else '存在しない'}")
    
    # deploy_snapshot/pagesディレクトリのファイルの場合
    deploy_file = r"c:\Users\user\Documents\GitHub\golf_score\deploy_snapshot\pages\06_結果確認.py"
    if os.path.exists(deploy_file):
        print(f"Deploy版のファイル: {deploy_file}")
        deploy_pages_dir = os.path.dirname(deploy_file)
        deploy_paths = [
            os.path.join(deploy_pages_dir, "ipaexg.ttf"),  # deploy_snapshot/pagesディレクトリ内
            os.path.join(os.path.dirname(deploy_pages_dir), "ipaexg.ttf"),  # deploy_snapshotディレクトリ
            os.path.join(os.path.dirname(os.path.dirname(deploy_pages_dir)), "ipaexg.ttf"),  # プロジェクトルート
        ]
        for path in deploy_paths:
            exists = os.path.exists(path)
            print(f"  {path} - {'存在する' if exists else '存在しない'}")
