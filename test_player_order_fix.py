#!/usr/bin/env python3
"""
プレイヤー名の並び順修正のテストスクリプト
member_id昇順での表示順序が正しく機能することを確認
"""

import os
import sys

# パスの設定
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from modules.round_results import get_round_results
from modules.supabase_client import get_supabase_client
from collections import OrderedDict
import pandas as pd

def test_get_round_results_order():
    """get_round_results()の結果がmember_id昇順になっているかテスト"""
    print("=== get_round_results()の順序テスト ===")
    
    try:
        # Supabaseクライアントを取得
        client = get_supabase_client()
        
        # 最新のラウンドを取得
        rounds_result = client.table('rounds').select('*').order('date_played', desc=True).limit(1).execute()
        
        if not rounds_result.data:
            print("テスト用のラウンドが見つかりません")
            return False
        
        latest_round = rounds_result.data[0]
        round_id = latest_round['round_id']
        print(f"テスト対象ラウンド: ID={round_id}, {latest_round['date_played']} - {latest_round['course_name']}")
        
        # get_round_results()を呼び出し
        round_results = get_round_results(round_id)
        
        if not round_results:
            print("round_resultsが空です")
            return False
        
        # 結果の順序をチェック
        member_ids = list(round_results.keys())
        print(f"取得されたmember_idの順序: {member_ids}")
        
        # member_idが昇順になっているかチェック
        is_sorted = member_ids == sorted(member_ids)
        print(f"member_idが昇順ソート済み: {is_sorted}")
        
        # OrderedDictかどうかをチェック
        is_ordered = isinstance(round_results, OrderedDict)
        print(f"OrderedDict形式: {is_ordered}")
        
        return is_sorted
        
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_dataframe_creation():
    """DataFrameの作成が正しく行われるかテスト"""
    print("\n=== DataFrame作成テスト ===")
    
    try:
        client = get_supabase_client()
        
        # 最新のラウンドを取得
        rounds_result = client.table('rounds').select('*').order('date_played', desc=True).limit(1).execute()
        latest_round = rounds_result.data[0]
        round_id = latest_round['round_id']
        
        # round_resultsを取得
        round_results = get_round_results(round_id)
        
        # scoresも取得（名前マッピング用）
        scores_result = client.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
        scores_data = sorted(scores_result.data, key=lambda x: x['member_id'])
        
        if not round_results or not scores_data:
            print("テストデータが不十分です")
            return False
        
        # プレイヤー名のマッピングを作成
        id_to_name = {score['member_id']: score['member']['name'] if score.get('member') else f"Player {score['member_id']}" for score in scores_data}
        
        # DataFrameを行指向で構築（修正後のコード）
        rows = []
        for member_id, data in round_results.items():
            row = {'名前': id_to_name.get(member_id, f"Player {member_id}")}
            row.update(data)
            rows.append(row)
        
        results_df = pd.DataFrame(rows)
        
        print("DataFrameの並び順（修正後）:")
        for i, name in enumerate(results_df['名前']):
            print(f"  {i+1}. {name}")
        
        # 期待される順序（scores_dataの名前順序）
        expected_names = [score['member']['name'] if score.get('member') else f"Player {score['member_id']}" for score in scores_data]
        actual_names = results_df['名前'].tolist()
        
        print("\n期待される順序:")
        for i, name in enumerate(expected_names):
            print(f"  {i+1}. {name}")
        
        # 順序が一致するかチェック
        order_match = actual_names == expected_names
        print(f"\n順序一致: {order_match}")
        
        if not order_match:
            print("不一致の詳細:")
            for i, (expected, actual) in enumerate(zip(expected_names, actual_names)):
                if expected != actual:
                    print(f"  位置{i+1}: 期待={expected}, 実際={actual}")
        
        return order_match
        
    except Exception as e:
        print(f"DataFrameテスト実行中にエラーが発生しました: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """メインテスト関数"""
    print("プレイヤー名並び順修正テスト開始\n")
    
    # テスト1: get_round_results()の順序確認
    test1_result = test_get_round_results_order()
    
    # テスト2: DataFrame作成の確認
    test2_result = test_dataframe_creation()
    
    print("\n=== テスト結果 ===")
    print(f"get_round_results()順序テスト: {'✓ 成功' if test1_result else '✗ 失敗'}")
    print(f"DataFrame作成テスト: {'✓ 成功' if test2_result else '✗ 失敗'}")
    
    overall_success = test1_result and test2_result
    print(f"\n総合結果: {'✓ 全テスト成功' if overall_success else '✗ 一部テスト失敗'}")
    
    if overall_success:
        print("\n修正が正常に機能しています！")
        print("バックスコア入力ページのラウンド結果でプレイヤー名が登録順（member_id昇順）で表示されるはずです。")
    else:
        print("\n修正に問題があります。詳細を確認してください。")

if __name__ == "__main__":
    main()
