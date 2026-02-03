import os
from dotenv import load_dotenv
from supabase import create_client
import streamlit as st
from modules.match_analyzer import create_match_matrix, create_detailed_match_results
from modules.game_points import calculate_total_game_points
import pandas as pd

def get_supabase_client():
    """Supabaseクライアントを取得"""
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Supabase credentials not found in environment variables")
    return create_client(url, key)

def recalculate_round_scores(round_id, scores, handicaps_data, has_extra=False):
    """特定のラウンドのスコアを再計算"""
    # プレイヤーデータの初期化
    player_data = {}
    for sc in scores:
        player_name = sc['member']['name'] if ('member' in sc and sc['member']) else f"Player {sc.get('member_id', 'Unknown')}"
        
        player_data[sc['member_id']] = {
            "Player": player_name,
            "Front Score": sc.get('front_score', 0) or 0,
            "Back Score": sc.get('back_score', 0) or 0,
            "Extra Score": sc.get('extra_score', 0) or 0,
            "Total Score": (sc.get('front_score', 0) or 0) + (sc.get('back_score', 0) or 0),
            # Game Point - 既存のデータを維持
            "Front GP": sc.get('front_game_pt', 0) or 0,
            "Back GP": sc.get('back_game_pt', 0) or 0,
            "Extra GP": sc.get('extra_game_pt', 0) or 0,
            "Game Pt": (sc.get('front_game_pt', 0) or 0) + (sc.get('back_game_pt', 0) or 0) + (sc.get('extra_game_pt', 0) or 0),
            # パットデータ
            "Front Putt": sc.get('front_putt', 0) or 0,
            "Back Putt": sc.get('back_putt', 0) or 0,
            "Extra Putt": sc.get('extra_putt', 0) or 0,
            # score_id を保持
            "score_id": sc.get('score_id'),
            # member_id を保持
            "member_id": sc.get('member_id')
        }

    # ハンディキャップデータの処理
    handicaps = {}
    total_only_set = set()
    if handicaps_data:
        for h in handicaps_data:
            handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
            handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
            if 'total_only' in h and h['total_only']:
                total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))

    # Game Point の計算（temp_game_ptとtotal_game_ptの計算）
    scores_list = []
    member_ids = []
    for member_id, data in player_data.items():
        member_ids.append(member_id)
        scores_list.append({
            'member_id': member_id,
            'front_score': data['Front Score'],
            'back_score': data['Back Score'],
            'extra_score': data['Extra Score']
        })
    
    game_points = calculate_total_game_points(scores_list)

    # マッチポイントの計算
    match_matrix = create_match_matrix(player_data, handicaps, total_only_set)
    match_results = create_detailed_match_results(player_data, handicaps, total_only_set)

    # 計算結果をプレイヤーデータに反映
    updates = []
    for player_id, data in player_data.items():
        player_name = data["Player"]
        # 該当プレイヤーの行を探す
        player_row = None
        for idx, row in match_results.iterrows():
            if idx == player_name:
                player_row = row
                break

        if player_row is not None:
            # マッチポイントの更新（整数に変換）
            update_data = {
                'score_id': data['score_id'],
                'match_front': int(float(player_row.get("Front", 0))),
                'match_back': int(float(player_row.get("Back", 0))),
                'match_total': int(float(player_row.get("Total", 0))),
                'match_extra': int(float(player_row.get("Extra", 0))) if has_extra else 0,
                'match_pt': int(float(player_row.get("Total Points", 0)))
            }
            
            # パットポイントの計算
            front_putt = data["Front Putt"]
            back_putt = data["Back Putt"]
            extra_putt = data.get("Extra Putt", 0)
            
            putt_points = calculate_putt_points(front_putt, back_putt, extra_putt, 
                                              list(player_data.values()), has_extra)
            update_data['putt_pt'] = int(putt_points)

            # Game Point の更新
            for member_game_points in game_points:
                if member_game_points['member_id'] == player_id:
                    update_data['temp_game_pt'] = member_game_points.get('temp_game_pt', 0)
                    update_data['total_game_pt'] = member_game_points.get('total_game_pt', 0)
                    break
            
            # トータルポイント計算（整数に変換）
            update_data['total_pt'] = int(
                update_data['total_game_pt'] +  # 新しく計算したゲームポイント
                update_data['match_pt'] +  # 新しく計算したマッチポイント
                update_data['putt_pt']  # 新しく計算したパットポイント
            )
            
            updates.append(update_data)

    return updates

def calculate_putt_points(front_putt, back_putt, extra_putt, all_players, has_extra):
    """パットポイントを計算"""
    # 全プレイヤーのパットデータを集める
    front_putts = [p.get('Front Putt', 0) for p in all_players if p.get('Front Putt', 0) > 0]
    back_putts = [p.get('Back Putt', 0) for p in all_players if p.get('Back Putt', 0) > 0]
    
    putt_points = 0
    
    # フロント9のパットポイント
    if front_putt > 0 and front_putts:
        min_front = min(front_putts)
        if front_putt == min_front:
            putt_points += 1
    
    # バック9のパットポイント
    if back_putt > 0 and back_putts:
        min_back = min(back_putts)
        if back_putt == min_back:
            putt_points += 1
    
    # エキストラホールのパットポイント
    if has_extra and extra_putt:
        extra_putts = [p.get('Extra Putt', 0) for p in all_players if p.get('Extra Putt', 0) > 0]
        if extra_putts:
            min_extra = min(extra_putts)
            if extra_putt == min_extra:
                putt_points += 1
    
    return putt_points

def recalculate_all_rounds():
    """全ラウンドのスコアを再計算"""
    print("Supabaseから全ラウンドのデータを再計算します...")
    
    try:
        supabase = get_supabase_client()
        
        # 全ラウンドを取得
        rounds_result = supabase.table('rounds').select('*').order('date_played').execute()
        if not rounds_result.data:
            print("ラウンドデータが見つかりません")
            return
        
        total_rounds = len(rounds_result.data)
        success_count = 0
        failed_count = 0
        print(f"合計 {total_rounds} ラウンドのデータを処理します")
        
        for i, round_data in enumerate(rounds_result.data, 1):
            round_id = round_data['round_id']
            print(f"\n処理中: ラウンド {round_id} ({i}/{total_rounds})")
            print(f"コース: {round_data['course_name']}")
            print(f"日付: {round_data['date_played']}")
            
            try:
                # スコアとハンディキャップデータを取得
                scores_result = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
                handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
                
                if not scores_result.data:
                    print(f"ラウンド {round_id} のスコアデータがありません")
                    failed_count += 1
                    continue
                
                # スコアの再計算
                updates = recalculate_round_scores(
                    round_id,
                    scores_result.data,
                    handicaps_result.data,
                    round_data.get('has_extra', False)
                )
                
                # スコアの更新を実行
                success = True
                for update in updates:
                    try:
                        score_id = update.pop('score_id')
                        # 更新データの内容を表示（デバッグ用）
                        print(f"レコードID {score_id} の更新データ:")
                        for key, value in update.items():
                            print(f"  {key}: {value}")
                        result = supabase.table('score').update(update).eq('score_id', score_id).execute()
                    except Exception as e:
                        print(f"スコアID {score_id} の更新に失敗: {str(e)}")
                        if hasattr(e, 'details'):
                            print(f"エラー詳細: {e.details}")
                        success = False
                
                if success:
                    success_count += 1
                    print(f"ラウンド {round_id} の再計算が完了しました ({len(updates)} 件のスコアを更新)")
                else:
                    failed_count += 1
                    print(f"ラウンド {round_id} の一部または全ての更新に失敗しました")
                
            except Exception as e:
                failed_count += 1
                print(f"ラウンド {round_id} の処理中にエラーが発生しました: {str(e)}")
                if hasattr(e, 'details'):
                    print(f"エラー詳細: {e.details}")
                continue
        
        print(f"\n全ラウンドの再計算が完了しました:")
        print(f"成功: {success_count} ラウンド")
        print(f"失敗: {failed_count} ラウンド")
        
    except Exception as e:
        print(f"処理中にエラーが発生しました: {str(e)}")
        if hasattr(e, 'details'):
            print(f"エラー詳細: {e.details}")
        raise

if __name__ == "__main__":
    recalculate_all_rounds()