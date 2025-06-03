#!/usr/bin/env python3
"""
scoreテーブルのスキーマを確認するスクリプト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.db import supabase

def check_score_table_schema():
    """scoreテーブルのスキーマを確認"""
    try:
        # サンプルレコードを1つ取得してフィールドを確認
        result = supabase.table('score').select('*').limit(1).execute()
        
        if result.data:
            sample_record = result.data[0]
            print("scoreテーブルの利用可能なフィールド:")
            for field in sample_record.keys():
                print(f"  - {field}: {type(sample_record[field])}")
        else:
            print("scoreテーブルにデータがありません")
            
        # テーブル情報を直接取得を試行
        print("\n=== テーブル構造の詳細確認 ===")
        
        # PostgreSQLの場合のスキーマ確認クエリ
        schema_query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'score'
        ORDER BY ordinal_position;
        """
        
        try:
            schema_result = supabase.rpc('sql', {'query': schema_query}).execute()
            if schema_result.data:
                print("スキーマ情報:")
                for col in schema_result.data:
                    print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        except Exception as e:
            print(f"スキーマ詳細取得失敗: {e}")
            
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    check_score_table_schema()
