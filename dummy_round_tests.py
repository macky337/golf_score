import streamlit as st
from modules.db import supabase
from datetime import datetime, timedelta
import time

# Streamlit警告設定は削除

def create_test_round(player_count, has_extra=False, date_offset=0):
    """テスト用のラウンドを作成する"""
    # メンバー取得
    members_result = supabase.table('member').select('*').limit(player_count).execute()
    members = members_result.data
    
    if not members or len(members) < player_count:
        print(f"必要な人数({player_count}人)のメンバーが見つかりません")
        return None

    # ラウンドを作成
    date_played = (datetime.now() + timedelta(days=date_offset)).strftime("%Y-%m-%d")
    round_data = {
        'date': date_played,
        'date_played': date_played,
        'course_name': f'テストコース_{player_count}人プレイ{"_Extra" if has_extra else ""}',
        'num_players': player_count,
        'has_extra': has_extra,
        'finalized': False
    }
    
    try:
        # ラウンドを作成
        round_result = supabase.table('rounds').insert(round_data).execute()
        if not round_result.data:
            print("ラウンドの作成に失敗しました")
            return None
        
        round_id = round_result.data[0]['round_id']
        print(f"ラウンド作成成功 - ID: {round_id}")
        
        # スコアデータを作成
        for i, member in enumerate(members[:player_count]):
            score_data = {
                'round_id': round_id,
                'member_id': member['member_id'],
                'front_score': 36 + i,
                'back_score': 38 + i,
                'front_putt': 13 + i,
                'back_putt': 15 + i
            }
            
            # 4人プレイの場合のゲームポイント
            if player_count == 4:
                if i == 0:
                    score_data['front_game_pt'] = 30
                    score_data['back_game_pt'] = 20
                elif i == 1:
                    score_data['front_game_pt'] = 10
                    score_data['back_game_pt'] = -10
                elif i == 2:
                    score_data['front_game_pt'] = -10
                    score_data['back_game_pt'] = -20
                else:
                    score_data['front_game_pt'] = -30
                    score_data['back_game_pt'] = 10
            # 3人プレイの場合のゲームポイント
            else:
                base_points = [40, 30, 20]
                score_data['front_game_pt'] = base_points[i]
                score_data['back_game_pt'] = base_points[i]
            
            # エキストラがある場合
            if has_extra:
                score_data['extra_score'] = 40 + i
                score_data['extra_putt'] = 16 + i
                if player_count == 4:
                    extra_points = [30, 10, -10, -30]
                    score_data['extra_game_pt'] = extra_points[i]
                else:
                    base_extra_points = [40, 30, 20]
                    score_data['extra_game_pt'] = base_extra_points[i]
            
            # スコア追加
            score_result = supabase.table('score').insert(score_data).execute()
            print(f"スコア作成成功 - プレイヤー: {member['name']}")
        
        # ハンディキャップデータ作成
        for i in range(player_count):
            for j in range(i + 1, player_count):
                handicap_data = {
                    'round_id': round_id,
                    'player_1_id': members[i]['member_id'],
                    'player_2_id': members[j]['member_id'],
                    'player_1_to_2': 0,
                    'player_2_to_1': 0,
                    'total_only': False
                }
                handicap_result = supabase.table('handicap_match').insert(handicap_data).execute()
                print(f"ハンディキャップ作成成功 - {members[i]['name']} vs {members[j]['name']}")
        
        return round_id
    
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return None

def run_all_tests():
    """テストケースを実行する"""
    results = []
    
    try:
        # テストケース1: 4人プレイ（エキストラあり）
        test1_id = create_test_round(4, True, 0)
        results.append(("テストケース1: 4人プレイ（エキストラあり）", test1_id))
        time.sleep(1)  # APIレート制限を避けるため
        
        # テストケース2: 4人プレイ（エキストラなし）
        test2_id = create_test_round(4, False, 1)
        results.append(("テストケース2: 4人プレイ（エキストラなし）", test2_id))
        time.sleep(1)
        
        # テストケース3: 3人プレイ（エキストラあり）
        test3_id = create_test_round(3, True, 2)
        results.append(("テストケース3: 3人プレイ（エキストラあり）", test3_id))
        time.sleep(1)
        
        # テストケース4: 3人プレイ（エキストラなし）
        test4_id = create_test_round(3, False, 3)
        results.append(("テストケース4: 3人プレイ（エキストラなし）", test4_id))
        
        print("\n==== テスト結果 ====")
        for name, round_id in results:
            print(f"{name}: {'成功 - ID: ' + str(round_id) if round_id else '失敗'}")
    
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    run_all_tests()
