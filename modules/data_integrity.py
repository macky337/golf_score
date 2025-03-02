import streamlit as st
from modules.db import supabase
import pandas as pd

def check_rounds_integrity():
    """ラウンドデータとスコアデータの整合性をチェックする"""
    # 全てのラウンド情報を取得
    rounds_result = supabase.table('rounds').select('*').order('round_id', desc=True).execute()
    rounds = rounds_result.data
    
    issues = []
    stats = {"total_rounds": len(rounds), "missing_scores": 0, "incomplete_scores": 0}
    
    for round_data in rounds:
        round_id = round_data['round_id']
        expected_players = round_data['num_players']
        
        # スコアデータを取得
        scores_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
        scores = scores_result.data
        
        if not scores:
            # スコアデータがない場合
            issues.append({
                "round_id": round_id,
                "date": round_data['date_played'],
                "course": round_data['course_name'],
                "issue": "スコアデータがありません",
                "expected_players": expected_players,
                "actual_players": 0,
                "severity": "高"
            })
            stats["missing_scores"] += 1
        elif len(scores) != expected_players:
            # プレイヤー数が一致しない場合
            issues.append({
                "round_id": round_id,
                "date": round_data['date_played'],
                "course": round_data['course_name'],
                "issue": f"プレイヤー数が一致しません（期待: {expected_players}, 実際: {len(scores)}）",
                "expected_players": expected_players,
                "actual_players": len(scores),
                "severity": "中"
            })
            stats["incomplete_scores"] += 1
    
    return issues, stats

def fix_missing_scores(round_id):
    """不足しているスコアデータを修復する"""
    # ラウンド情報を取得
    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    if not round_result.data:
        return False, "ラウンド情報が見つかりません"
        
    round_data = round_result.data[0]
    
    # 既存のスコアを取得
    existing_scores = supabase.table('score').select('*').eq('round_id', round_id).execute()
    existing_member_ids = [s['member_id'] for s in existing_scores.data] if existing_scores.data else []
    
    # このラウンドに参加したメンバーIDを取得
    handicaps_result = supabase.table('handicap_match').select('player_1_id, player_2_id').eq('round_id', round_id).execute()
    participant_ids = set()
    
    if handicaps_result.data:
        for h in handicaps_result.data:
            participant_ids.add(h['player_1_id'])
            participant_ids.add(h['player_2_id'])
    else:
        # ハンディキャップデータがない場合、すべてのメンバーから選択させる
        members_result = supabase.table('member').select('member_id').execute()
        if not members_result.data:
            return False, "メンバー情報が見つかりません"
            
        return False, "ハンディキャップデータが存在しないため、修復できません"
    
    # 不足しているメンバーのスコアを作成
    missing_member_ids = [mid for mid in participant_ids if mid not in existing_member_ids]
    
    if not missing_member_ids:
        return False, "不足しているスコアはありません"
    
    # 最大のスコアIDを取得
    max_id_result = supabase.table('score').select('score_id').order('score_id', desc=True).limit(1).execute()
    next_score_id = 1
    if max_id_result.data:
        next_score_id = max_id_result.data[0]['score_id'] + 1
    
    # 不足しているスコアを作成
    success_count = 0
    for member_id in missing_member_ids:
        try:
            score_data = {
                'score_id': next_score_id,
                'round_id': round_id,
                'member_id': member_id,
                'front_score': 0,
                'back_score': 0,
                'extra_score': 0,
                'front_putt': 0,
                'back_putt': 0,
                'extra_putt': 0,
                'front_game_pt': 0,
                'back_game_pt': 0,
                'extra_game_pt': 0,
                'match_pt': 0,
                'put_pt': 0,
                'total_pt': 0
            }
            supabase.table('score').insert(score_data).execute()
            next_score_id += 1
            success_count += 1
        except Exception as e:
            return False, f"スコア作成中にエラーが発生しました: {str(e)}"
    
    # ラウンドのnum_playersを実際のプレイヤー数と一致させる
    total_players = len(existing_member_ids) + success_count
    supabase.table('rounds').update({'num_players': total_players}).eq('round_id', round_id).execute()
    
    return True, f"{success_count}件のスコアデータを作成しました"
