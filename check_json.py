#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSONファイルの内容と有効性をチェック
"""

import json
import os

def check_json_file(filename):
    """JSONファイルをチェック"""
    try:
        print(f"\n=== {filename} ===")
        if not os.path.exists(filename):
            print(f"ファイルが存在しません: {filename}")
            return False
            
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("ファイル内容:")
        print(repr(content[:200]))  # 最初の200文字のみ表示
        
        # JSONとしてパース
        data = json.loads(content)
        print("✓ 有効なJSONです")
        print(f"内容: {data}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"✗ JSONパースエラー: {e}")
        return False
    except Exception as e:
        print(f"✗ その他のエラー: {e}")
        return False

def main():
    """メイン処理"""
    files_to_check = [
        'version.json',
        'deploy_metrics.json',
        'deploy_metrics.json.temp'
    ]
    
    print("JSONファイルチェック開始...")
    
    all_ok = True
    for filename in files_to_check:
        if not check_json_file(filename):
            all_ok = False
    
    print(f"\n結果: {'すべてOK' if all_ok else '修正が必要'}")

if __name__ == "__main__":
    main()
