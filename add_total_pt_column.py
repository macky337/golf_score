#!/usr/bin/env python3
"""
round_resultsテーブルにtotal_ptカラムを追加し、既存データの値を計算して設定するスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.supabase_client import get_supabase_client

def main():
    """round_resultsテーブルにtotal_ptカラムを追加し、既存データを更新"""
    print("=== round_results テーブル total_pt カラム追加ツール ===")
    
    # 環境変数の読み込み
    load_dotenv()
    
    # Supabaseクライアント初期化
    supabase = get_supabase_client()
    
    print("\n注意: このスクリプトはテーブルスキーマを変更します。")
    print("実行前にデータベースのバックアップを取ることを強く推奨します。")
    
    confirm = input("\n続行しますか？ [y/N]: ")
    if confirm.lower() != 'y':
        print("処理をキャンセルしました。")
        return
    
    try:
        # 1. total_ptカラムの存在確認
        print("\n1. テーブル構造の確認...")
        result = supabase.table('round_results').select('*').limit(1).execute()
        
        if result.data and 'total_pt' in result.data[0]:
            print("✓ total_ptカラムは既に存在します。")
            update_existing = input("既存の値を再計算して更新しますか？ [y/N]: ")
            if update_existing.lower() != 'y':
                print("処理を終了します。")
                return
        else:
            print("ℹ total_ptカラムが存在しません。")
            print("\n注意: Supabaseでカラム追加にはSQLエディタでの手動実行が必要です。")
            print("以下のSQLをSupabaseのSQLエディタで実行してください：")
            print("\n    ALTER TABLE round_results ADD COLUMN total_pt NUMERIC DEFAULT 0;")
            print("\nSQLの実行が完了したら、このスクリプトを再実行してください。")
            return
        
        # 2. 既存データの更新
        print("\n2. 既存データの更新...")
        all_results = supabase.table('round_results').select('*').execute().data
        
        update_count = 0
        error_count = 0
        
        for record in all_results:
            try:
                # total_ptを計算
                match_pt = record.get('match_pt', 0) or 0
                putt_pt = record.get('putt_pt', 0) or 0
                total_game_pt = record.get('total_game_pt', 0) or 0
                calculated_total_pt = match_pt + putt_pt + total_game_pt
                
                # 現在の値と比較
                current_total_pt = record.get('total_pt', 0) or 0
                
                if abs(calculated_total_pt - current_total_pt) > 0.01:
                    # 値を更新
                    supabase.table('round_results').update({
                        'total_pt': calculated_total_pt
                    }).eq('id', record['id']).execute()
                    
                    update_count += 1
                    print(f"  更新: ID {record['id']} -> {calculated_total_pt}")
                
            except Exception as e:
                error_count += 1
                print(f"  エラー: ID {record.get('id', 'unknown')} - {e}")
        
        print(f"\n処理完了:")
        print(f"  更新件数: {update_count}")
        print(f"  エラー件数: {error_count}")
        print(f"  総レコード数: {len(all_results)}")
        
        if update_count > 0:
            print("\n✓ total_ptカラムの値が正常に更新されました。")
        else:
            print("\n✓ すべてのレコードが既に正しい値を持っています。")
            
    except Exception as e:
        print(f"\n✗ 処理中にエラーが発生しました: {e}")
        return

if __name__ == "__main__":
    main()