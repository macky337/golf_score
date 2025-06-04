#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHANGELOG読み込み修正の動作確認スクリプト
"""

import os
import sys

def simulate_changelog_loading():
    """main_fixed.pyのshow_changelog関数の動作をシミュレート"""
    print("=== CHANGELOG読み込み修正テスト ===")
    
    try:
        # スクリプトのディレクトリを基準にCHANGELOG.mdのパスを構築
        script_dir = os.path.dirname(os.path.abspath(__file__))
        changelog_path = os.path.join(script_dir, "CHANGELOG.md")
        
        print(f"スクリプトディレクトリ: {script_dir}")
        print(f"CHANGELOGパス: {changelog_path}")
        print(f"ファイル存在確認: {os.path.exists(changelog_path)}")
        
        if os.path.exists(changelog_path):
            with open(changelog_path, "r", encoding="utf-8") as f:
                changelog = f.read()
            
            print("✅ CHANGELOG読み込み成功！")
            print(f"ファイルサイズ: {len(changelog)} 文字")
            print(f"最初の200文字:\n{changelog[:200]}...")
            return True
        else:
            print(f"❌ CHANGELOG.mdファイルが見つかりません: {changelog_path}")
            return False
            
    except Exception as e:
        print(f"❌ 読み込みエラー: {str(e)}")
        
        # デバッグ情報を追加
        script_dir = os.path.dirname(os.path.abspath(__file__))
        changelog_path = os.path.join(script_dir, "CHANGELOG.md")
        print(f"探索パス: {changelog_path}")
        print(f"ファイル存在確認: {os.path.exists(changelog_path)}")
        
        if os.path.exists(script_dir):
            files = os.listdir(script_dir)
            md_files = [f for f in files if f.endswith('.md')]
            print(f"ディレクトリ内のMDファイル: {md_files}")
        
        return False

if __name__ == "__main__":
    success = simulate_changelog_loading()
    print(f"\nテスト結果: {'成功' if success else '失敗'}")
