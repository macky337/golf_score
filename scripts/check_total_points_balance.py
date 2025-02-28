#!/usr/bin/env python3
"""
各ラウンドごとにtotal_ptの合計が±0になっているか確認するスクリプト
また、game_pt, match_pt, put_ptの合計がtotal_ptと一致しているかも確認します。
"""

import os
import sys
import pandas as pd
from decimal import Decimal

# インポートパスを修正
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.db import supabase

def get_all_rounds():
    """確定済みのラウンドIDを取得"""
    try:
        rounds_result = supabase.table('rounds').select('round_id,date_played,course_name').eq('finalized', True).execute()
        return rounds_result.data
    except Exception as e:
        print(f"ラウンド一覧の取得中にエラーが発生しました: {str(e)}")
        return []

def check_round_points(round_id):
    """指定されたラウンドIDのポイントバランスをチェック"""
    try:
        scores_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
        scores = scores_result.data
        
        if not scores:
            print(f"ラウンドID {round_id}: スコアデータがありません。")
            return False, None, None
        
        # 各スコアからポイントを抽出
        points_data = []
        for score in scores:
            member_id = score.get('member_id')
            
            # ゲームポイント
            front_game_pt = score.get('front_game_pt') or 0
            back_game_pt = score.get('back_game_pt') or 0
            extra_game_pt = score.get('extra_game_pt') or 0
            game_pt = front_game_pt + back_game_pt + extra_game_pt
            
            # マッチポイントと パットポイント
            match_pt = score.get('match_pt') or 0
            put_pt = score.get('put_pt') or 0
            
            # DBに保存されているトータルポイント
            stored_total_pt = score.get('total_pt') or 0
            
            # 再計算したトータルポイント
            calculated_total_pt = game_pt + match_pt + put_pt
            
            # 格納
            points_data.append({
                'member_id': member_id,
                'game_pt': game_pt,
                'match_pt': match_pt,
                'put_pt': put_pt,
                'stored_total_pt': stored_total_pt,
                'calculated_total_pt': calculated_total_pt
            })
        
        # DataFrameに変換して集計
        df = pd.DataFrame(points_data)
        
        # 各ポイントの合計を計算
        total_game_pt = df['game_pt'].sum()
        total_match_pt = df['match_pt'].sum()
        total_put_pt = df['put_pt'].sum()
        total_stored_pt = df['stored_total_pt'].sum()
        total_calculated_pt = df['calculated_total_pt'].sum()
        
        # 小数点の誤差を吸収するために小数点以下を切り捨て
        total_game_pt = round(total_game_pt, 6)
        total_match_pt = round(total_match_pt, 6)
        total_put_pt = round(total_put_pt, 6)
        total_stored_pt = round(total_stored_pt, 6)
        total_calculated_pt = round(total_calculated_pt, 6)
        
        # 合計ポイントが0か確認
        is_balanced = (total_calculated_pt == 0)
        
        # 各プレイヤーの計算値と保存値が一致しているか確認
        is_consistent = True
        for _, row in df.iterrows():
            if row['stored_total_pt'] != row['calculated_total_pt']:
                is_consistent = False
                break
        
        # まとめ
        summary = {
            'round_id': round_id,
            'player_count': len(df),
            'total_game_pt': total_game_pt,
            'total_match_pt': total_match_pt,
            'total_put_pt': total_put_pt,
            'total_stored_pt': total_stored_pt,
            'total_calculated_pt': total_calculated_pt,
            'is_balanced': is_balanced,
            'is_consistent': is_consistent
        }
        
        return True, df, summary
        
    except Exception as e:
        print(f"ラウンドID {round_id} のチェック中にエラーが発生しました: {str(e)}")
        return False, None, None

def update_round_total_pt(round_id):
    """指定されたラウンドのtotal_ptを再計算して更新する"""
    try:
        scores_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
        scores = scores_result.data
        
        update_count = 0
        
        for score in scores:
            # ゲームポイント
            front_game_pt = score.get('front_game_pt') or 0
            back_game_pt = score.get('back_game_pt') or 0
            extra_game_pt = score.get('extra_game_pt') or 0
            game_pt = front_game_pt + back_game_pt + extra_game_pt
            
            # マッチポイントと パットポイント
            match_pt = score.get('match_pt') or 0
            put_pt = score.get('put_pt') or 0
            
            # 再計算したトータルポイント
            calculated_total_pt = game_pt + match_pt + put_pt
            
            # 保存されているトータルポイント
            stored_total_pt = score.get('total_pt') or 0
            
            # 値が異なる場合は更新
            if calculated_total_pt != stored_total_pt:
                update_result = supabase.table('score').update(
                    {'total_pt': calculated_total_pt}
                ).eq('score_id', score['score_id']).execute()
                
                if update_result:
                    update_count += 1
        
        return update_count
    
    except Exception as e:
        print(f"ラウンドID {round_id} の更新中にエラーが発生しました: {str(e)}")
        return 0

def main():
    print("スコアテーブルでラウンドごとのtotal_ptの合計が±0になっているかチェックします...")
    
    # ラウンド一覧を取得
    rounds = get_all_rounds()
    
    if not rounds:
        print("確定済みのラウンドが見つかりません。")
        return
    
    print(f"全{len(rounds)}ラウンドをチェックします。\n")
    
    # 結果を格納するリスト
    balanced_rounds = []
    unbalanced_rounds = []
    inconsistent_rounds = []
    
    # 各ラウンドをチェック
    for round_info in rounds:
        round_id = round_info['round_id']
        success, df, summary = check_round_points(round_id)
        
        if success and summary:
            date_info = f"{round_info.get('date_played', '不明')} - {round_info.get('course_name', '不明')}"
            
            if not summary['is_consistent']:
                # 保存値と計算値が一致していない
                inconsistent_rounds.append((round_id, date_info, summary))
            elif not summary['is_balanced']:
                # バランスが取れていない
                unbalanced_rounds.append((round_id, date_info, summary))
            else:
                # 問題なし
                balanced_rounds.append((round_id, date_info, summary))
    
    # 結果の表示
    print("\n===== チェック結果 =====")
    print(f"バランスが取れているラウンド: {len(balanced_rounds)}/{len(rounds)}")
    print(f"バランスが取れていないラウンド: {len(unbalanced_rounds)}/{len(rounds)}")
    print(f"計算値と保存値が一致していないラウンド: {len(inconsistent_rounds)}/{len(rounds)}")
    
    # 不整合があるラウンドの詳細表示
    if unbalanced_rounds:
        print("\n----- バランスが取れていないラウンド -----")
        for round_id, date_info, summary in unbalanced_rounds:
            print(f"ラウンドID: {round_id} ({date_info})")
            print(f"  プレイヤー数: {summary['player_count']}")
            print(f"  Game Pt合計: {summary['total_game_pt']}")
            print(f"  Match Pt合計: {summary['total_match_pt']}")
            print(f"  Put Pt合計: {summary['total_put_pt']}")
            print(f"  DB上のTotal Pt合計: {summary['total_stored_pt']}")
            print(f"  計算上のTotal Pt合計: {summary['total_calculated_pt']}")
            print("")
    
    if inconsistent_rounds:
        print("\n----- 計算値と保存値が一致していないラウンド -----")
        for round_id, date_info, summary in inconsistent_rounds:
            print(f"ラウンドID: {round_id} ({date_info})")
            print(f"  プレイヤー数: {summary['player_count']}")
            print(f"  Game Pt合計: {summary['total_game_pt']}")
            print(f"  Match Pt合計: {summary['total_match_pt']}")
            print(f"  Put Pt合計: {summary['total_put_pt']}")
            print(f"  DB上のTotal Pt合計: {summary['total_stored_pt']}")
            print(f"  計算上のTotal Pt合計: {summary['total_calculated_pt']}")
            print("")
    
    # 修正するか確認
    if inconsistent_rounds:
        fix = input("計算値と保存値が一致していないラウンドを修正しますか？ (y/n): ")
        if fix.lower() == 'y':
            fixed_count = 0
            for round_id, _, _ in inconsistent_rounds:
                update_count = update_round_total_pt(round_id)
                if update_count > 0:
                    fixed_count += 1
                    print(f"ラウンドID: {round_id} - {update_count}件のスコアを修正しました。")
            
            print(f"\n合計 {fixed_count}/{len(inconsistent_rounds)} ラウンドの不整合を修正しました。")

if __name__ == "__main__":
    main()