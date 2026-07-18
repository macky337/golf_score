import streamlit as st
import pandas as pd
from modules.match_analyzer import create_match_matrix, create_detailed_match_results
from modules.calculation_logic import calculate_player_points
from modules.supabase_client import get_supabase_client

def recalculate_all_rounds(progress_callback=None):
    """すべてのラウンドのスコアを再計算する"""
    supabase = get_supabase_client()
    
    # すべてのラウンドを取得
    rounds_result = supabase.table('rounds').select('*').order('date_played').execute()
    
    if not rounds_result.data:
        return "ラウンドデータが見つかりません。"
    
    total_rounds = len(rounds_result.data)
    success_count = 0
    failed_rounds = []
    
    # 各ラウンドに対して処理
    for i, round_data in enumerate(rounds_result.data):
        round_id = round_data['round_id']
        if progress_callback:
            progress_callback(f"ラウンド {round_id}: {round_data['course_name']} ({i+1}/{total_rounds}) 処理中...")
        
        try:
            # スコアデータとハンディキャップデータを取得
            scores_result = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
            handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
            
            if not scores_result.data:
                failed_rounds.append(f"ラウンド {round_id}: スコアデータなし")
                continue
                
            if not handicaps_result.data:
                failed_rounds.append(f"ラウンド {round_id}: ハンディキャップデータなし")
                continue
            
            # 再計算処理
            updated_scores = process_round_scores(scores_result.data, handicaps_result.data, round_data)
            
            # 更新データを準備
            for score in updated_scores:
                member_id = score['member_id']
                
                # 更新データを作成
                update_data = {
                    'match_front': score['match_front'],
                    'match_back': score['match_back'],
                    'match_total': score['match_total'],
                    'match_extra': score['match_extra'],
                    'match_pt': score['match_pt'],
                    'putt_pt': score['putt_pt'],
                    'total_pt': score['total_pt']
                }
                
                # ゲームポイントは既存のものを保持
                
                # データを更新
                supabase.table('score').update(update_data).eq('score_id', score['score_id']).execute()
            
            success_count += 1
            
            if progress_callback:
                progress_callback(f"ラウンド {round_id}: 更新成功")
                
        except Exception as e:
            failed_rounds.append(f"ラウンド {round_id}: エラー - {str(e)}")
            if progress_callback:
                progress_callback(f"ラウンド {round_id}: 更新失敗 - {str(e)}")
    
    # 結果レポートを作成
    report = f"処理完了: {success_count}/{total_rounds} ラウンドを更新しました。\n"
    if failed_rounds:
        report += f"失敗: {len(failed_rounds)}件\n"
        for failure in failed_rounds:
            report += f"- {failure}\n"
    
    return report

def process_round_scores(scores, handicaps_data, round_data):
    """ラウンドのスコアを処理して再計算する"""
    player_data = {}
    
    # スコアデータを処理
    for sc in scores:
        player_name = sc['member']['name'] if ('member' in sc and sc['member']) else f"Player {sc.get('member_id', 'Unknown')}"
        
        player_data[sc['member_id']] = {
            "Player": player_name,
            "Front Score": sc.get('front_score', 0) or 0,
            "Back Score": sc.get('back_score', 0) or 0,
            "Extra Score": sc.get('extra_score', 0) or 0,
            "Total Score": (sc.get('front_score', 0) or 0) + (sc.get('back_score', 0) or 0),
            # Game Point関連 - 既存のデータを使用
            "Front GP": sc.get('front_game_pt', 0) or 0,
            "Back GP": sc.get('back_game_pt', 0) or 0,
            "Extra GP": sc.get('extra_game_pt', 0) or 0,
            "Game Pt": (sc.get('front_game_pt', 0) or 0) + (sc.get('back_game_pt', 0) or 0) + (sc.get('extra_game_pt', 0) or 0),
            # Putt関連
            "Front Putt": sc.get('front_putt', 0) or 0,
            "Back Putt": sc.get('back_putt', 0) or 0,
            "Extra Putt": sc.get('extra_putt', 0) or 0,
            # score_id を保持
            "score_id": sc.get('score_id'),
            "member_id": sc['member_id']
        }
    
    # ハンディキャップデータを処理
    handicaps = {}
    total_only_set = set()
    if handicaps_data:
        for h in handicaps_data:
            handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
            handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
            if 'total_only' in h and h['total_only']:
                total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))
    
    # マッチポイントを計算
    match_matrix = create_match_matrix(player_data, handicaps, total_only_set)
    match_results = create_detailed_match_results(player_data, handicaps, total_only_set)
    
    # 計算結果を反映
    for player_id in player_data:
        # マッチポイント
        player_name = player_data[player_id]["Player"]
        if player_name in match_results.index:
            row = match_results.loc[player_name]
            player_data[player_id]["Match Front"] = row["Front"]
            player_data[player_id]["Match Back"] = row["Back"]
            player_data[player_id]["Match Total"] = row["Total"]
            player_data[player_id]["Match Extra"] = row["Extra"]
            player_data[player_id]["Match Pt"] = row["Total Points"]
        
        # パットポイント計算
        front_putt = player_data[player_id]["Front Putt"]
        back_putt = player_data[player_id]["Back Putt"]
        extra_putt = player_data[player_id]["Extra Putt"]
        
        # パットポイントの計算方法をアプリケーションの仕様に合わせて実装
        # (ここではシンプルな例としてパット数が少ない方がポイント高として実装)
        putt_points = calculate_putt_points(front_putt, back_putt, extra_putt, list(player_data.values()), round_data.get('has_extra', False))
        player_data[player_id]["Putt Pt"] = putt_points
        
        # トータルポイント計算
        game_pt = player_data[player_id]["Game Pt"]
        match_pt = player_data[player_id]["Match Pt"]
        putt_pt = player_data[player_id]["Putt Pt"]
        player_data[player_id]["Total Pt"] = game_pt + match_pt + putt_pt
    
    # 更新するためのデータ形式に変換
    updated_scores = []
    for player_id, data in player_data.items():
        updated_scores.append({
            'score_id': data['score_id'],
            'member_id': player_id,
            'match_front': data['Match Front'],
            'match_back': data['Match Back'],
            'match_total': data['Match Total'],
            'match_extra': data['Match Extra'],
            'match_pt': data['Match Pt'],
            'putt_pt': data['Putt Pt'],
            'total_pt': data['Total Pt']
        })
    
    return updated_scores

def calculate_putt_points(front_putt, back_putt, extra_putt, all_players, has_extra):
    """パットポイントを計算する関数"""
    # 全プレイヤーのパットデータを集める
    front_putts = [p.get('Front Putt', 0) for p in all_players]
    back_putts = [p.get('Back Putt', 0) for p in all_players]
    
    # フロント9のパットポイント
    front_putt_points = 0
    if front_putt and any(front_putts):
        min_front = min(p for p in front_putts if p > 0)
        if front_putt == min_front:
            front_putt_points = 1
    
    # バック9のパットポイント
    back_putt_points = 0
    if back_putt and any(back_putts):
        min_back = min(p for p in back_putts if p > 0)
        if back_putt == min_back:
            back_putt_points = 1
    
    # エキストラホールのパットポイント
    extra_putt_points = 0
    if has_extra and extra_putt:
        extra_putts = [p.get('Extra Putt', 0) for p in all_players]
        if any(extra_putts):
            min_extra = min(p for p in extra_putts if p > 0)
            if extra_putt == min_extra:
                extra_putt_points = 1
    
    # 合計パットポイント
    return front_putt_points + back_putt_points + extra_putt_points

if __name__ == "__main__":
    print(recalculate_all_rounds())
