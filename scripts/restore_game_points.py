#!/usr/bin/env python3
"""
スコアデータを復旧するスクリプト
バックアップファイルからゲームポイントとパットデータを読み込み、
現在のスコアデータに適用し、マッチポイントとパットポイントを再計算します。
"""

import json
import os
import sys
from collections import Counter

# インポートパスを修正
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.db import supabase

# バックアップファイルのパス
BACKUP_FILES = [
    # ゲームポイントデータを含むバックアップ
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups", "main_backup_20250225_140419.json"),
    # パットデータを含むバックアップ
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups", "golf_score_backup_20250219_231345.json"),
    # その他のバックアップ
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups", "remote_main_backup_20250225_140525.json")
]

def load_backup_data(file_path):
    """バックアップファイルからデータを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"バックアップファイルの読み込み中にエラーが発生しました: {str(e)}")
        return None

def print_data_sample(backup_data, data_type="all"):
    """バックアップデータのサンプルを表示"""
    if 'scores' in backup_data and backup_data['scores']:
        sample_score = backup_data['scores'][0]
        print(f"{data_type}データのサンプル:")
        if data_type == "all" or data_type == "putt":
            print(f"  front_putt: {sample_score.get('front_putt')}")
            print(f"  back_putt: {sample_score.get('back_putt')}")
            print(f"  extra_putt: {sample_score.get('extra_putt')}")
        if data_type == "all" or data_type == "game":
            print(f"  front_game_pt: {sample_score.get('front_game_pt')}")
            print(f"  back_game_pt: {sample_score.get('back_game_pt')}")
            print(f"  extra_game_pt: {sample_score.get('extra_game_pt')}")

def find_backup_with_data(data_type="game"):
    """指定されたデータタイプ（ゲームポイント or パットデータ）を含むバックアップを見つける"""
    for backup_file in BACKUP_FILES:
        if os.path.exists(backup_file):
            backup_data = load_backup_data(backup_file)
            if backup_data and 'scores' in backup_data and backup_data['scores']:
                sample_score = backup_data['scores'][0]
                
                if data_type == "game":
                    # ゲームポイントデータがあるかチェック
                    has_game_data = (sample_score.get('front_game_pt') is not None or 
                                    sample_score.get('back_game_pt') is not None or 
                                    sample_score.get('extra_game_pt') is not None)
                    if has_game_data:
                        print(f"ゲームポイントデータが見つかりました: {backup_file}")
                        print_data_sample(backup_data, "game")
                        return backup_file, backup_data
                
                elif data_type == "putt":
                    # パットデータがあるかチェック
                    has_putt_data = (sample_score.get('front_putt') is not None or 
                                    sample_score.get('back_putt') is not None or 
                                    sample_score.get('extra_putt') is not None)
                    if has_putt_data:
                        print(f"パットデータが見つかりました: {backup_file}")
                        print_data_sample(backup_data, "putt")
                        return backup_file, backup_data
    
    return None, None

def update_scores_from_backup(backup_data, update_type="all"):
    """バックアップからスコアデータを更新する"""
    if not backup_data or 'scores' not in backup_data:
        print("バックアップデータにスコア情報がありません。")
        return False
    
    score_updates = 0
    game_pt_updates = 0
    putt_updates = 0
    errors = 0
    
    for score in backup_data['scores']:
        try:
            # スコアIDに基づいて更新
            score_id = score['score_id']
            update_data = {}
            
            if update_type == "all" or update_type == "game":
                # ゲームポイントデータ
                front_game_pt = score.get('front_game_pt')
                back_game_pt = score.get('back_game_pt')
                extra_game_pt = score.get('extra_game_pt')
                
                has_game_data = False
                
                if front_game_pt is not None:
                    update_data['front_game_pt'] = front_game_pt
                    has_game_data = True
                if back_game_pt is not None:
                    update_data['back_game_pt'] = back_game_pt
                    has_game_data = True
                if extra_game_pt is not None:
                    update_data['extra_game_pt'] = extra_game_pt
                    has_game_data = True
                
                if has_game_data:
                    game_pt_updates += 1
            
            if update_type == "all" or update_type == "putt":
                # パットデータ
                front_putt = score.get('front_putt')
                back_putt = score.get('back_putt')
                extra_putt = score.get('extra_putt')
                
                has_putt_data = False
                
                if front_putt is not None:
                    update_data['front_putt'] = front_putt
                    has_putt_data = True
                if back_putt is not None:
                    update_data['back_putt'] = back_putt
                    has_putt_data = True
                if extra_putt is not None:
                    update_data['extra_putt'] = extra_putt
                    has_putt_data = True
                    
                if has_putt_data:
                    putt_updates += 1
            
            # 更新するデータがある場合のみ実行
            if update_data:
                supabase.table('score').update(update_data).eq('score_id', score_id).execute()
                score_updates += 1
                
                # 詳細ログ
                game_info = f"front_game_pt: {update_data.get('front_game_pt')}, back_game_pt: {update_data.get('back_game_pt')}, extra_game_pt: {update_data.get('extra_game_pt')}" if 'front_game_pt' in update_data else "なし"
                putt_info = f"front_putt: {update_data.get('front_putt')}, back_putt: {update_data.get('back_putt')}, extra_putt: {update_data.get('extra_putt')}" if 'front_putt' in update_data else "なし"
                print(f"スコアID: {score_id} を更新しました (ゲームポイント: {game_info}, パットデータ: {putt_info})")
        
        except Exception as e:
            print(f"スコアID: {score['score_id']} の更新中にエラーが発生しました: {str(e)}")
            errors += 1
    
    print(f"合計 {score_updates} 件のスコアを更新しました（ゲームポイントあり: {game_pt_updates}件, パットデータあり: {putt_updates}件）。エラー数: {errors}")
    return score_updates > 0

def recalculate_match_points(round_id):
    """ラウンドのマッチポイントを再計算する"""
    try:
        # ラウンドのスコアデータを取得
        scores_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
        scores = scores_result.data
        
        # ハンディキャップデータを取得
        handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
        handicaps = handicaps_result.data
        
        # ハンディキャップをペアごとにマッピング
        handicap_map = {}
        total_only_pairs = set()
        for h in handicaps:
            handicap_map[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
            handicap_map[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
            if h['total_only']:
                total_only_pairs.add(frozenset([h['player_1_id'], h['player_2_id']]))

        # スコアの計算
        for score in scores:
            front_total = score['front_score']
            back_total = score['back_score']
            extra_total = score['extra_score'] if score['extra_score'] is not None else 0
            
            # マッチポイントの初期化
            front_match_points = 0
            back_match_points = 0
            total_match_points = 0
            extra_match_points = 0
            
            # 他のプレイヤーとの対戦結果を計算
            for opponent in scores:
                if score['member_id'] == opponent['member_id']:
                    continue
                
                pair = frozenset([score['member_id'], opponent['member_id']])
                is_total_only = pair in total_only_pairs
                
                # ハンディキャップを取得
                handicap = handicap_map.get((score['member_id'], opponent['member_id']), 0)
                
                # ネットスコアの計算
                net_front = front_total - (0 if is_total_only else handicap//2)
                net_back = back_total - (0 if is_total_only else (handicap - handicap//2))
                net_extra = extra_total - handicap if extra_total is not None and extra_total > 0 else 0
                
                opp_handicap = handicap_map.get((opponent['member_id'], score['member_id']), 0)
                opp_net_front = opponent['front_score'] - (0 if is_total_only else opp_handicap//2)
                opp_net_back = opponent['back_score'] - (0 if is_total_only else (opp_handicap - opp_handicap//2))
                opp_net_extra = opponent['extra_score'] - opp_handicap if opponent['extra_score'] is not None and opponent['extra_score'] > 0 else 0
                
                # マッチポイントの計算
                if not is_total_only:
                    # Front 9
                    if net_front < opp_net_front:
                        front_match_points += 5
                    elif net_front > opp_net_front:
                        front_match_points -= 5
                    
                    # Back 9
                    if net_back < opp_net_back:
                        back_match_points += 5
                    elif net_back > opp_net_back:
                        back_match_points -= 5
                
                # Total
                net_total = front_total + back_total - handicap
                opp_net_total = opponent['front_score'] + opponent['back_score'] - opp_handicap
                if net_total < opp_net_total:
                    total_match_points += 10
                elif net_total > opp_net_total:
                    total_match_points -= 10
                
                # Extra holes（もしあれば）
                if extra_total is not None and extra_total > 0 and opponent['extra_score'] is not None and opponent['extra_score'] > 0:
                    if net_extra < opp_net_extra:
                        extra_match_points += 5
                    elif net_extra > opp_net_extra:
                        extra_match_points -= 5
            
            # マッチポイント合計
            match_pt = front_match_points + back_match_points + total_match_points + extra_match_points
            
            # スコアの更新
            supabase.table('score').update({
                'match_front': front_match_points,
                'match_back': back_match_points,
                'match_total': total_match_points,
                'match_extra': extra_match_points,
                'match_pt': match_pt
            }).eq('score_id', score['score_id']).execute()
            
        return True

    except Exception as e:
        print(f"マッチポイントの再計算中にエラーが発生しました: {str(e)}")
        return False

def calculate_put_points(round_id):
    """ラウンドのパットポイントを計算する
    
    パット戦の得点計算（4人 or 3人の場合）
    
    4人の場合:
      - 1名のみが最少 → 最少者+30pt、残り3名-10pt
      - 2名同点最少 → 最少2名+10pt、残り2名-10pt
      - 3名同点最少 → 最少3名+10pt、残り1名-30pt
      - 全員同点 → 0pt
      
    3人の場合:
      - 1名のみが最少 → 最少者+20pt、残り2名-10pt
      - 2名同点最少 → 最少2名+5pt、残り1名-10pt
      - 全員同点 → 0pt
    """
    try:
        # スコアデータを取得
        scores_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
        scores = scores_result.data
        
        if not scores:
            print(f"ラウンドID: {round_id} のスコアデータが見つかりません")
            return False
        
        # プレイヤー数を確認
        player_count = len(scores)
        if player_count < 3:
            print(f"ラウンドID: {round_id} のプレイヤー数が少なすぎます: {player_count}人")
            return False
            
        print(f"ラウンドID: {round_id} のパットデータ:")
        
        # ラウンド内の全プレイヤーのパットデータを集計
        putt_data = {}
        for score in scores:
            member_id = score['member_id']
            front_putt = score.get('front_putt') or 0
            back_putt = score.get('back_putt') or 0
            extra_putt = score.get('extra_putt') or 0
            total_putt = front_putt + back_putt + extra_putt
            
            putt_data[member_id] = {
                'score_id': score['score_id'],
                'total_putt': total_putt,
                'front_putt': front_putt,
                'back_putt': back_putt,
                'extra_putt': extra_putt
            }
            print(f"  プレイヤーID: {member_id} - front: {front_putt}, back: {back_putt}, extra: {extra_putt}, 合計: {total_putt}")
        
        # パット数の少ない順にソート
        sorted_putts = sorted(putt_data.items(), key=lambda x: x[1]['total_putt'])
        
        # パット数の出現回数をカウント
        putt_counts = Counter(item[1]['total_putt'] for item in sorted_putts)
        
        # 最少のパット数と、それを出したプレーヤー数を取得
        min_putt = sorted_putts[0][1]['total_putt']
        num_min_putters = putt_counts[min_putt]
        
        print(f"  最少パット数: {min_putt}, 最少達成人数: {num_min_putters}")
        
        # プレイヤー数に応じてポイントを計算
        put_points = {}
        
        if player_count == 4:
            # 4人の場合
            if num_min_putters == 1:
                # 1名のみが最少
                for member_id, data in putt_data.items():
                    if data['total_putt'] == min_putt:
                        put_points[member_id] = 30  # 最少者+30pt
                    else:
                        put_points[member_id] = -10  # 残り3名-10pt
            
            elif num_min_putters == 2:
                # 2名同点最少
                for member_id, data in putt_data.items():
                    if data['total_putt'] == min_putt:
                        put_points[member_id] = 10  # 最少2名+10pt
                    else:
                        put_points[member_id] = -10  # 残り2名-10pt
            
            elif num_min_putters == 3:
                # 3名同点最少
                for member_id, data in putt_data.items():
                    if data['total_putt'] == min_putt:
                        put_points[member_id] = 10  # 最少3名+10pt
                    else:
                        put_points[member_id] = -30  # 残り1名-30pt
            
            else:  # num_min_putters == 4
                # 全員同点
                for member_id in putt_data.keys():
                    put_points[member_id] = 0  # 全員0pt
        
        elif player_count == 3:
            # 3人の場合
            if num_min_putters == 1:
                # 1名のみが最少
                for member_id, data in putt_data.items():
                    if data['total_putt'] == min_putt:
                        put_points[member_id] = 20  # 最少者+20pt
                    else:
                        put_points[member_id] = -10  # 残り2名-10pt
            
            elif num_min_putters == 2:
                # 2名同点最少
                for member_id, data in putt_data.items():
                    if data['total_putt'] == min_putt:
                        put_points[member_id] = 5  # 最少2名+5pt
                    else:
                        put_points[member_id] = -10  # 残り1名-10pt
            
            else:  # num_min_putters == 3
                # 全員同点
                for member_id in putt_data.keys():
                    put_points[member_id] = 0  # 全員0pt
        
        else:
            # 5人以上の場合は例外的なケースとして、独自のルールを適用するか、無視する
            print(f"  注意: 5人以上のルール未定義のため、パットポイントは0となります。")
            for member_id in putt_data.keys():
                put_points[member_id] = 0
        
        # 計算されたポイントをデータベースに保存
        for member_id, pt in put_points.items():
            score_id = putt_data[member_id]['score_id']
            print(f"  プレイヤーID: {member_id} - スコアID: {score_id} - パット数: {putt_data[member_id]['total_putt']} - ポイント: {pt}")
            
            # スコア更新
            supabase.table('score').update({
                'put_pt': pt
            }).eq('score_id', score_id).execute()
        
        return True
    
    except Exception as e:
        print(f"パットポイントの計算中にエラーが発生しました: {str(e)}")
        return False

def recalculate_total_points():
    """すべての確定済みラウンドに対してポイント再計算"""
    try:
        # 確定済みのラウンドを取得
        rounds_result = supabase.table('rounds').select('round_id').eq('finalized', True).execute()
        
        if not rounds_result.data:
            print("確定済みのラウンドが見つかりません。")
            return False
        
        round_ids = [r['round_id'] for r in rounds_result.data]
        rounds_updated = 0
        
        for round_id in round_ids:
            try:
                print(f"ラウンドID: {round_id} のマッチポイントを再計算中...")
                # マッチポイントの再計算
                recalculate_match_points(round_id)
                
                print(f"ラウンドID: {round_id} のパットポイントを再計算中...")
                # パットポイントの計算
                calculate_put_points(round_id)
                
                # スコアデータを取得
                scores_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
                scores = scores_result.data
                
                for score in scores:
                    # Game Ptの計算
                    front_game_pt = score.get('front_game_pt') or 0
                    back_game_pt = score.get('back_game_pt') or 0
                    extra_game_pt = score.get('extra_game_pt') or 0
                    game_pt_sum = front_game_pt + back_game_pt + extra_game_pt
                    
                    # Match Ptを取得
                    match_pt = score.get('match_pt') or 0
                    
                    # Put Ptを取得
                    put_pt = score.get('put_pt') or 0
                    
                    # Total Ptの再計算
                    total_pt = game_pt_sum + match_pt + put_pt
                    
                    print(f"  スコアID: {score['score_id']} - ゲーム: {game_pt_sum}, マッチ: {match_pt}, パット: {put_pt}, 合計: {total_pt}")
                    
                    # 更新データ - game_ptカラムは存在しないのでtotal_ptのみ更新
                    update_data = {
                        'total_pt': total_pt
                    }
                    
                    # スコアの更新
                    supabase.table('score').update(update_data).eq('score_id', score['score_id']).execute()
                
                rounds_updated += 1
                print(f"ラウンドID: {round_id} のポイントを再計算しました")
            
            except Exception as e:
                print(f"ラウンドID: {round_id} の再計算中にエラーが発生しました: {str(e)}")
        
        print(f"合計 {rounds_updated} 件のラウンドのポイントを再計算しました。")
        return rounds_updated > 0
    
    except Exception as e:
        print(f"ポイント再計算中にエラーが発生しました: {str(e)}")
        return False

def get_available_backups():
    """利用可能なバックアップファイルを一覧表示"""
    backups_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
    json_files = [f for f in os.listdir(backups_dir) if f.endswith('.json')]
    
    print("利用可能なバックアップファイル:")
    for i, file in enumerate(json_files, 1):
        file_path = os.path.join(backups_dir, file)
        mod_time = os.path.getmtime(file_path)
        size = os.path.getsize(file_path) / 1024
        print(f"{i}. {file} (更新: {mod_time}, サイズ: {size:.2f} KB)")
    
    return json_files

def verify_game_points():
    """ゲームポイントが正しく復元されたかを検証"""
    try:
        # いくつかのラウンドからサンプルスコアを取得
        rounds_result = supabase.table('rounds').select('round_id').limit(5).execute()
        
        if not rounds_result.data:
            print("ラウンドデータが見つかりません")
            return False
        
        for r in rounds_result.data:
            round_id = r['round_id']
            scores_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
            scores = scores_result.data
            
            print(f"\nラウンドID: {round_id} のゲームポイントとパットデータ:")
            for s in scores:
                print(f"  スコアID: {s['score_id']}, プレイヤーID: {s['member_id']}")
                print(f"    front_game_pt: {s.get('front_game_pt')}")
                print(f"    back_game_pt: {s.get('back_game_pt')}")
                print(f"    extra_game_pt: {s.get('extra_game_pt')}")
                print(f"    front_putt: {s.get('front_putt')}")
                print(f"    back_putt: {s.get('back_putt')}")
                print(f"    extra_putt: {s.get('extra_putt')}")
                print(f"    match_pt: {s.get('match_pt')}")
                print(f"    put_pt: {s.get('put_pt')}")
                print(f"    total_pt: {s.get('total_pt')}")
        
        return True
    except Exception as e:
        print(f"データ検証中にエラーが発生しました: {str(e)}")
        return False

def restore_scores_from_backup():
    """バックアップからスコアデータを復元する"""
    print("スコアデータの復旧を開始します...")
    
    # 1. ゲームポイントデータの復元（main_backup_20250225_140419.json から）
    game_backup_file, game_backup_data = None, None
    for backup_file in BACKUP_FILES:
        if "main_backup_20250225_140419.json" in backup_file and os.path.exists(backup_file):
            print(f"ゲームポイント復旧用のバックアップファイルを見つけました: {backup_file}")
            game_backup_data = load_backup_data(backup_file)
            game_backup_file = backup_file
            break
    
    if not game_backup_file:
        print("指定されたゲームポイントバックアップファイルが見つかりません。別のバックアップを検索します。")
        game_backup_file, game_backup_data = find_backup_with_data("game")
    
    if not game_backup_data:
        print("ゲームポイントデータを含むバックアップが見つかりませんでした。")
        return False
    
    # 2. パットデータの復元（既存のファイルから）
    putt_backup_file, putt_backup_data = find_backup_with_data("putt")
    
    if not putt_backup_data:
        print("パットデータを含むバックアップが見つかりませんでした。")
        # パットデータが見つからなくてもゲームポイントだけでも復旧を続行
    
    # 3. ゲームポイントデータの復旧
    print(f"\nゲームポイントデータの復旧を開始します（ソース: {game_backup_file}）...")
    if not update_scores_from_backup(game_backup_data, "game"):
        print("ゲームポイントデータの復旧に失敗しました。")
        return False
    
    # 4. パットデータの復旧（あれば）
    if putt_backup_data:
        print(f"\nパットデータの復旧を開始します（ソース: {putt_backup_file}）...")
        update_scores_from_backup(putt_backup_data, "putt")
    
    # 5. ポイントの再計算
    print("\n各種ポイントを再計算中...")
    if not recalculate_total_points():
        print("ポイント再計算に失敗しました。")
        return False
    
    print("\nスコアデータの復旧が完了しました。")
    return True

if __name__ == "__main__":
    print("スコアデータ復旧スクリプトを実行します...")
    
    try:
        if restore_scores_from_backup():
            print("\n復旧処理が正常に完了しました。")
            print("\n復旧後のデータを検証します...")
            verify_game_points()
            sys.exit(0)
        else:
            print("\n復旧処理中にエラーが発生しました。")
            sys.exit(1)
    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {str(e)}")
        sys.exit(1)