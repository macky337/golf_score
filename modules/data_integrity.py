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

def verify_putt_points(round_id):
    """指定されたラウンドのパットポイント計算が正しいかを検証"""
    try:
        # スコアデータを取得
        scores_result = supabase.table('score').select(
            '*, member(name)'
        ).eq('round_id', round_id).execute()
        scores = scores_result.data
        
        if not scores:
            return {"status": "error", "message": "スコアデータがありません"}
        
        # プレイヤー数を確認
        n_players = len(scores)
        
        # パットスコアの取得
        front_putts = {s['member_id']: s['front_putt'] or 0 for s in scores}
        back_putts = {s['member_id']: s['back_putt'] or 0 for s in scores}
        extra_putts = {s['member_id']: s['extra_putt'] or 0 for s in scores if s['extra_putt']}
        
        # 実際に保存されているパットポイント
        actual_putt_pts = {s['member_id']: s['put_pt'] or 0 for s in scores}
        
        # パットポイントの計算（フロント）
        front_pts = recalculate_putt_points(front_putts, n_players)
        
        # パットポイントの計算（バック）
        back_pts = recalculate_putt_points(back_putts, n_players)
        
        # パットポイントの計算（エキストラ）
        extra_pts = recalculate_putt_points(extra_putts, n_players) if extra_putts else {}
        
        # 合計ポイント
        total_pts = {}
        for mid in actual_putt_pts.keys():
            front_pt = front_pts.get(mid, 0)
            back_pt = back_pts.get(mid, 0)
            extra_pt = extra_pts.get(mid, 0)
            total_pts[mid] = front_pt + back_pt + extra_pt
        
        # 検証結果
        result = {
            "round_id": round_id,
            "player_count": n_players,
            "players": [],
            "is_correct": True,
            "differences": []
        }
        
        for s in scores:
            player_info = {
                "member_id": s['member_id'],
                "name": s['member']['name'],
                "front_putt": front_putts[s['member_id']],
                "back_putt": back_putts[s['member_id']],
                "extra_putt": extra_putts.get(s['member_id'], 0) if extra_putts else 0,
                "actual_put_pt": actual_putt_pts[s['member_id']],
                "calculated_put_pt": total_pts[s['member_id']],
                "front_pt": front_pts.get(s['member_id'], 0),
                "back_pt": back_pts.get(s['member_id'], 0),
                "extra_pt": extra_pts.get(s['member_id'], 0) if extra_putts else 0
            }
            
            # 再計算した値と実際の値を比較
            if abs(player_info["actual_put_pt"] - player_info["calculated_put_pt"]) > 0.01:
                result["is_correct"] = False
                result["differences"].append({
                    "player": player_info["name"],
                    "actual": player_info["actual_put_pt"],
                    "calculated": player_info["calculated_put_pt"],
                    "diff": player_info["actual_put_pt"] - player_info["calculated_put_pt"]
                })
            
            result["players"].append(player_info)
        
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

def recalculate_putt_points(putt_scores, n_players):
    """パット戦の得点計算（関数のコピー）"""
    if not putt_scores:  # スコアが空の場合
        return {}
        
    scores = list(putt_scores.values())
    min_score = min(scores)
    winners = [m_id for m_id, score in putt_scores.items() if score == min_score]
    points = {m_id: 0 for m_id in putt_scores}
    
    if n_players == 3:
        if len(winners) == 1:
            points[winners[0]] = 20  # 最少が1名の場合は+20pt
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = -10  # 残り2名は-10pt
        elif len(winners) == 2:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 5  # 最少が2名の場合は+5pt
                else:
                    points[m_id] = -10  # 残り1名は-10pt
        # 全員同点の場合は初期値の0のまま
    elif n_players == 4:
        if len(winners) == 1:
            points[winners[0]] = 30  # 最少が1名の場合は+30pt
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = -10  # 残り3名は-10pt
        elif len(winners) == 2:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 10  # 最少が2名の場合は+10pt
                else:
                    points[m_id] = -10  # 残り2名は-10pt
        elif len(winners) == 3:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 10  # 最少が3名の場合は+10pt
                else:
                    points[m_id] = -30  # 残り1名は-30pt
        # 全員同点の場合は初期値の0のまま
    
    return points
