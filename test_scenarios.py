from modules.supabase_client import get_supabase_client
from datetime import date, timedelta
import streamlit as st
from modules.debug import handle_error

def create_test_round(player_ids, course_name, date_played, has_extra=False):
    """テストラウンドを作成"""
    supabase = get_supabase_client()
    
    # 最新のround_idを取得して+1する
    latest_round = supabase.table('rounds').select('round_id').order('round_id', desc=True).limit(1).execute()
    next_round_id = latest_round.data[0]['round_id'] + 1 if latest_round.data else 1
    
    # ラウンド作成
    round_data = {
        'round_id': next_round_id,
        'date': date_played,
        'date_played': date_played,
        'course_name': course_name,
        'num_players': len(player_ids),
        'has_extra': has_extra,
        'finalized': False
    }
    
    try:
        result = supabase.table('rounds').insert(round_data).execute()
        if not result.data:
            raise Exception("ラウンドの作成に失敗しました")
        
        round_id = result.data[0]['round_id']
        
        # 最新のhandicap_match idを取得
        latest_match = supabase.table('handicap_match').select('id').order('id', desc=True).limit(1).execute()
        next_match_id = latest_match.data[0]['id'] + 1 if latest_match.data else 1
        
        # ハンディキャップマッチ設定
        for i in range(len(player_ids)):
            for j in range(i + 1, len(player_ids)):
                handicap_data = {
                    'id': next_match_id,
                    'round_id': round_id,
                    'player_1_id': player_ids[i],
                    'player_2_id': player_ids[j],
                    'player_1_to_2': 0,
                    'player_2_to_1': 0,
                    'total_only': False
                }
                supabase.table('handicap_match').insert(handicap_data).execute()
                next_match_id += 1
        
        # スコア初期データ作成
        # 最新のscore_idを取得
        latest_score = supabase.table('score').select('score_id').order('score_id', desc=True).limit(1).execute()
        next_score_id = latest_score.data[0]['score_id'] + 1 if latest_score.data else 1
        
        for player_id in player_ids:
            score_data = {
                'score_id': next_score_id,
                'round_id': round_id,
                'member_id': player_id,
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
                'putt_pt': 0,  # put_pt から putt_pt に修正
                'total_pt': 0,
                'temp_game_pt': 0,
                'total_game_pt': 0
            }
            supabase.table('score').insert(score_data).execute()
            next_score_id += 1
        
        return round_id
    except Exception as e:
        print(f"ラウンド作成中にエラーが発生しました: {str(e)}")
        raise

def update_scores(round_id, scores_data):
    """スコアを更新"""
    supabase = get_supabase_client()
    
    for player_id, data in scores_data.items():
        supabase.table('score').update(data).eq('round_id', round_id).eq('member_id', player_id).execute()

def clear_test_data():
    """テストデータをクリアする"""
    supabase = get_supabase_client()
    
    try:
        # テストコースのラウンドIDを取得
        test_rounds = supabase.table('rounds').select('round_id').ilike('course_name', 'テストコース%').execute()
        if test_rounds.data:
            round_ids = [r['round_id'] for r in test_rounds.data]
            
            # スコアデータを削除
            for round_id in round_ids:
                supabase.table('score').delete().eq('round_id', round_id).execute()
                
                # ハンディキャップマッチデータを削除
                supabase.table('handicap_match').delete().eq('round_id', round_id).execute()
                
                # ラウンドデータを削除
                supabase.table('rounds').delete().eq('round_id', round_id).execute()
            
            print(f"{len(round_ids)}件のテストデータを削除しました")
        else:
            print("削除対象のテストデータはありませんでした")
            
    except Exception as e:
        print(f"テストデータの削除中にエラーが発生しました: {str(e)}")

def test_four_players():
    """4人プレイのテストケース"""
    players = [1, 2, 3, 4]  # プレイヤーID
    start_date = date.today()
    
    # テストケース1: 標準的なスコア分布
    round_id = create_test_round(players, "テストコース1", str(start_date))
    scores = {
        1: {'front_score': 45, 'back_score': 44, 'front_putt': 16, 'back_putt': 15},
        2: {'front_score': 42, 'back_score': 43, 'front_putt': 15, 'back_putt': 16},
        3: {'front_score': 48, 'back_score': 46, 'front_putt': 17, 'back_putt': 14},
        4: {'front_score': 44, 'back_score': 45, 'front_putt': 14, 'back_putt': 17}
    }
    update_scores(round_id, scores)
    print(f"4人プレイ テストケース1作成完了: ラウンドID {round_id}")
    
    # テストケース2: 接戦のスコア
    round_id = create_test_round(players, "テストコース2", str(start_date + timedelta(days=1)))
    scores = {
        1: {'front_score': 45, 'back_score': 45, 'front_putt': 15, 'back_putt': 15},
        2: {'front_score': 44, 'back_score': 46, 'front_putt': 16, 'back_putt': 15},
        3: {'front_score': 46, 'back_score': 44, 'front_putt': 15, 'back_putt': 16},
        4: {'front_score': 45, 'back_score': 45, 'front_putt': 15, 'back_putt': 15}
    }
    update_scores(round_id, scores)
    print(f"4人プレイ テストケース2作成完了: ラウンドID {round_id}")
    
    # テストケース3: エキストラホールあり
    round_id = create_test_round(players, "テストコース3", str(start_date + timedelta(days=2)), has_extra=True)
    scores = {
        1: {'front_score': 43, 'back_score': 44, 'extra_score': 4, 'front_putt': 15, 'back_putt': 15, 'extra_putt': 2},
        2: {'front_score': 44, 'back_score': 43, 'extra_score': 5, 'front_putt': 16, 'back_putt': 14, 'extra_putt': 2},
        3: {'front_score': 45, 'back_score': 45, 'extra_score': 4, 'front_putt': 14, 'back_putt': 16, 'extra_putt': 1},
        4: {'front_score': 42, 'back_score': 46, 'extra_score': 6, 'front_putt': 15, 'back_putt': 15, 'extra_putt': 3}
    }
    update_scores(round_id, scores)
    print(f"4人プレイ テストケース3作成完了: ラウンドID {round_id}")

def test_three_players():
    """3人プレイのテストケース"""
    players = [1, 2, 3]  # プレイヤーID
    start_date = date.today() + timedelta(days=3)
    
    # テストケース1: 標準的なスコア分布
    round_id = create_test_round(players, "テストコース4", str(start_date))
    scores = {
        1: {'front_score': 45, 'back_score': 44, 'front_putt': 16, 'back_putt': 15},
        2: {'front_score': 42, 'back_score': 43, 'front_putt': 15, 'back_putt': 16},
        3: {'front_score': 48, 'back_score': 46, 'front_putt': 17, 'back_putt': 14}
    }
    update_scores(round_id, scores)
    print(f"3人プレイ テストケース1作成完了: ラウンドID {round_id}")
    
    # テストケース2: 接戦のスコア
    round_id = create_test_round(players, "テストコース5", str(start_date + timedelta(days=1)))
    scores = {
        1: {'front_score': 45, 'back_score': 45, 'front_putt': 15, 'back_putt': 15},
        2: {'front_score': 44, 'back_score': 46, 'front_putt': 16, 'back_putt': 15},
        3: {'front_score': 46, 'back_score': 44, 'front_putt': 15, 'back_putt': 16}
    }
    update_scores(round_id, scores)
    print(f"3人プレイ テストケース2作成完了: ラウンドID {round_id}")
    
    # テストケース3: エキストラホールあり
    round_id = create_test_round(players, "テストコース6", str(start_date + timedelta(days=2)), has_extra=True)
    scores = {
        1: {'front_score': 43, 'back_score': 44, 'extra_score': 4, 'front_putt': 15, 'back_putt': 15, 'extra_putt': 2},
        2: {'front_score': 44, 'back_score': 43, 'extra_score': 5, 'front_putt': 16, 'back_putt': 14, 'extra_putt': 2},
        3: {'front_score': 45, 'back_score': 45, 'extra_score': 4, 'front_putt': 14, 'back_putt': 16, 'extra_putt': 1}
    }
    update_scores(round_id, scores)
    print(f"3人プレイ テストケース3作成完了: ラウンドID {round_id}")

if __name__ == "__main__":
    print("古いテストデータを削除します...")
    clear_test_data()
    
    print("\nテストケースの作成を開始します...")
    test_four_players()
    print("\n3人プレイのテストケースを作成します...")
    test_three_players()
    print("\nすべてのテストケースの作成が完了しました。")