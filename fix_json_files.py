#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSONファイルからコメント行を削除するスクリプト
"""

import os
import re
import json
from pathlib import Path

def fix_json_file(file_path):
    """JSONファイルからコメント行を削除し、有効なJSONに修正"""
    try:
        print(f"修正中: {file_path}")
        
        # ファイルをバイナリモードで読み取り
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # UTF-8でデコード
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            # cp932でデコードを試行
            text = content.decode('cp932')
        
        # BOMを削除
        if text.startswith('\ufeff'):
            text = text[1:]
        
        # 行に分割
        lines = text.split('\n')
        
        # コメント行（// で始まる行）を削除
        filtered_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped.startswith('//'):
                filtered_lines.append(line)
        
        # 空の行を先頭から削除
        while filtered_lines and not filtered_lines[0].strip():
            filtered_lines.pop(0)
        
        # 結合
        cleaned_text = '\n'.join(filtered_lines)
        
        # JSONとして有効か確認
        try:
            json.loads(cleaned_text)
            print(f"  ✓ 有効なJSONです")
        except json.JSONDecodeError as e:
            print(f"  ✗ JSONエラー: {e}")
            return False
        
        # UTF-8 BOMなしで保存
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        print(f"  ✓ 修正完了: {file_path}")
        return True
        
    except Exception as e:
        print(f"  ✗ エラー: {e}")
        return False

def main():
    """メイン処理"""
    current_dir = Path(__file__).parent
    
    # JSONファイルを検索
    json_files = list(current_dir.glob('*.json'))
    
    print(f"発見されたJSONファイル: {len(json_files)}個")
    
    for json_file in json_files:
        if json_file.name.endswith('.temp'):
            continue
        fix_json_file(json_file)
    
    # .tempファイルも処理
    temp_files = list(current_dir.glob('*.json.temp'))
    for temp_file in temp_files:
        fix_json_file(temp_file)
    
    print("\n修正完了!")

if __name__ == "__main__":
    main()
