#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全JSONファイルからコメント行を自動削除する最終スクリプト
"""

import os
import json
import re
from pathlib import Path

def clean_json_file(file_path):
    """JSONファイルからコメント行を完全に削除"""
    try:
        print(f"処理中: {file_path}")
        
        # ファイルをバイナリで読み取り
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        
        # UTF-8またはcp932でデコード
        try:
            content = raw_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = raw_content.decode('cp932')
            except UnicodeDecodeError:
                content = raw_content.decode('utf-8', errors='ignore')
        
        # BOM削除
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # 行に分割してコメント行を削除
        lines = content.split('\n')
        clean_lines = []
        
        for line in lines:
            stripped = line.strip()
            # //で始まるコメント行を除外
            if not stripped.startswith('//'):
                clean_lines.append(line)
        
        # 空行を先頭から削除
        while clean_lines and not clean_lines[0].strip():
            clean_lines.pop(0)
        
        # 結合
        clean_content = '\n'.join(clean_lines)
        
        # JSONとして検証
        try:
            json.loads(clean_content)
            print(f"  ✓ 有効なJSON")
        except json.JSONDecodeError as e:
            print(f"  ✗ JSONエラー: {e}")
            return False
        
        # UTF-8で保存
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(clean_content)
        
        print(f"  ✓ 修正完了")
        return True
        
    except Exception as e:
        print(f"  ✗ エラー: {e}")
        return False

def main():
    """メイン処理"""
    current_dir = Path(__file__).parent
    
    # 処理対象のJSONファイル
    json_files = [
        'version.json',
        'deploy_metrics.json',
        'deploy_metrics.json.temp'
    ]
    
    print("=== JSONファイル自動修正開始 ===")
    
    success_count = 0
    for json_file in json_files:
        file_path = current_dir / json_file
        if file_path.exists():
            if clean_json_file(file_path):
                success_count += 1
        else:
            print(f"ファイルが存在しません: {json_file}")
    
    print(f"\n=== 完了: {success_count}個のファイルを修正 ===")

if __name__ == "__main__":
    main()
