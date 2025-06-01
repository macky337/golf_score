#!/usr/bin/env python3
"""
パット計算ロジックのテスト用スクリプト
"""
import sqlite3
import pandas as pd
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.score_calculator import calc_putt_points

def test_calculation():
    # データベース接続
    conn = sqlite3.connect('data/scores.db')
    
    # 最新のラウンドデータを確認
    print('=== 最新のラウンドデータ ===')
    rounds = pd.read_sql_query('SELECT * FROM rounds ORDER BY date DESC LIMIT 5', conn)
    print(rounds)
    
    if rounds.empty:
        print("ラウンドデータが見つかりません。")
        conn.close()
        return
    
    print('\n=== 最新のスコアデータ ===')
    latest_round = rounds.iloc[0]['id']
    scores = pd.read_sql_query(f'SELECT * FROM scores WHERE round_id = {latest_round}', conn)
    print(f'ラウンドID {latest_round} のスコア:')
    print(scores)
    
    player_count = len(scores)
    print(f'\nプレイヤー数: {player_count}')
    
    # パット計算のテスト
    if player_count >= 3:
        print('\n=== パット計算ロジックのテスト ===')
        
        # テストケース1: 4人プレイで3人が同点最小の場合
        test_scores_4p_3winners = [1, 1, 1, 3]  # 3人が1パット、1人が3パット
        test_players_4p = [1, 2, 3, 4]
        
        print(f'テストケース1（4人、3人同点最小）: {test_scores_4p_3winners}')
        result1 = calc_putt_points(test_players_4p, test_scores_4p_3winners)
        print(f'結果: {result1}')
        expected = [5, 5, 5, -15]  # 新しいロジック
        print(f'期待値: {expected}')
        print(f'正しい: {result1 == expected}')
        
        # テストケース2: 4人プレイで1人が最小の場合
        test_scores_4p_1winner = [1, 2, 2, 2]  # 1人が1パット、3人が2パット
        
        print(f'\nテストケース2（4人、1人最小）: {test_scores_4p_1winner}')
        result2 = calc_putt_points(test_players_4p, test_scores_4p_1winner)
        print(f'結果: {result2}')
        expected2 = [15, -5, -5, -5]
        print(f'期待値: {expected2}')
        print(f'正しい: {result2 == expected2}')
        
        # テストケース3: 3人プレイで全員同点の場合
        test_scores_3p_all_tie = [2, 2, 2]
        test_players_3p = [1, 2, 3]
        
        print(f'\nテストケース3（3人、全員同点）: {test_scores_3p_all_tie}')
        result3 = calc_putt_points(test_players_3p, test_scores_3p_all_tie)
        print(f'結果: {result3}')
        expected3 = [0, 0, 0]
        print(f'期待値: {expected3}')
        print(f'正しい: {result3 == expected3}')
    
    conn.close()

if __name__ == "__main__":
    test_calculation()
