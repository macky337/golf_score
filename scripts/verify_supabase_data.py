import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import sys

def verify_supabase_data(round_id=None):
    """Supabaseのデータを確認"""
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("環境変数が設定されていません")
    
    supabase = create_client(url, key)
    
    # 特定のラウンドIDが指定された場合
    if round_id:
        print(f"\n=== ラウンドID {round_id} の詳細確認 ===")
        
        # ラウンド情報の取得
        round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
        if round_result.data:
            print("\nラウンド基本情報:")
            round_data = round_result.data[0]
            print(f"ラウンドID: {round_data['round_id']}")
            print(f"日付: {round_data['date']}")
            print(f"プレイ日: {round_data['date_played']}")
            print(f"コース名: {round_data['course_name']}")
            print(f"プレイヤー数: {round_data['num_players']}")
            print(f"エキストラホール: {'あり' if round_data['has_extra'] else 'なし'}")
            print(f"確定状態: {'確定済み' if round_data['finalized'] else '未確定'}")
            print(f"作成日時: {round_data['created_at']}")
        else:
            print(f"ラウンドID {round_id} は存在しません")
            return
            
        # スコア情報の取得
        score_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
        if score_result.data:
            print(f"\nスコア情報（{len(score_result.data)}件）:")
            for i, score in enumerate(score_result.data, 1):
                print(f"\n[プレイヤー {i}]")
                print(f"スコアID: {score['score_id']}")
                print(f"メンバーID: {score['member_id']}")
                print(f"スコア（F/B/E）: {score['front_score']}/{score['back_score']}/{score['extra_score'] if score['extra_score'] is not None else 'なし'}")
                print(f"パット（F/B/E）: {score['front_putt']}/{score['back_putt']}/{score['extra_putt'] if score['extra_putt'] is not None else 'なし'}")
                print(f"ゲームポイント（F/B/E）: {score['front_game_pt']}/{score['back_game_pt']}/{score['extra_game_pt'] if score['extra_game_pt'] is not None else 'なし'}")
                print(f"マッチポイント（F/B/T/E）: {score['match_front']}/{score['match_back']}/{score['match_total']}/{score['match_extra'] if score['match_extra'] is not None else 'なし'}")
                print(f"トータルポイント: {score['total_pt']}")
                print(f"作成日時: {score['created_at']}")
        else:
            print(f"ラウンドID {round_id} のスコアデータはありません")
        
        # ハンディキャップマッチ情報の取得
        match_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
        if match_result.data:
            print(f"\nハンディキャップマッチ情報（{len(match_result.data)}件）:")
            for i, match in enumerate(match_result.data, 1):
                print(f"\n[マッチ {i}]")
                print(f"マッチID: {match['id']}")
                print(f"プレイヤー: {match['player_1_id']} vs {match['player_2_id']}")
                print(f"ハンディキャップ 1→2: {match['player_1_to_2']}")
                print(f"ハンディキャップ 2→1: {match['player_2_to_1']}")
                print(f"トータルオンリー: {'はい' if match['total_only'] else 'いいえ'}")
                print(f"作成日時: {match['created_at']}")
        else:
            print(f"ラウンドID {round_id} のハンディキャップマッチデータはありません")
    
    else:
        # 通常の確認処理（既存のコード）
        print("\n=== scoreテーブルの確認 ===")
        result = supabase.table('score').select('*').order('created_at', desc=True).execute()
        
        if result.data:
            print(f"総スコア数: {len(result.data)}")
            print("\n最新データ（新しい順に3件）:")
            for score in result.data[:3]:
                print(f"\nスコアID: {score['score_id']}")
                print(f"ラウンドID: {score['round_id']}")
                print(f"作成日時: {score['created_at']}")
                print(f"game_pt: {score['front_game_pt']}/{score['back_game_pt']}/{score['extra_game_pt'] if score['extra_game_pt'] is not None else 'なし'}")
        else:
            print("スコアデータが見つかりません")
        
        # handicap_matchデータの確認
        print("\n=== handicap_matchテーブルの確認 ===")
        result = supabase.table('handicap_match').select('*').order('created_at', desc=True).execute()
        
        if result.data:
            print(f"総ハンディキャップマッチ数: {len(result.data)}")
            print("\n最新データ（新しい順に3件）:")
            for match in result.data[:3]:
                print(f"\nID: {match['id']}")
                print(f"ラウンドID: {match['round_id']}")
                print(f"プレイヤー: {match['player_1_id']} vs {match['player_2_id']}")
                print(f"作成日時: {match['created_at']}")
        else:
            print("ハンディキャップマッチデータが見つかりません")
        
        # 現在の日付と最新データの日付を比較
        if result.data and len(result.data) > 0:
            current_date = datetime.now()
            
            try:
                # scoreテーブルの最新データ
                score_result = supabase.table('score').select('created_at').order('created_at', desc=True).limit(1).execute()
                if score_result.data:
                    latest_score_date = score_result.data[0]['created_at']
                    print(f"\nscoreテーブルの最新データ日時: {latest_score_date}")
                
                # handicap_matchテーブルの最新データ
                match_result = supabase.table('handicap_match').select('created_at').order('created_at', desc=True).limit(1).execute()
                if match_result.data:
                    latest_match_date = match_result.data[0]['created_at']
                    print(f"handicap_matchテーブルの最新データ日時: {latest_match_date}")
            except Exception as e:
                print(f"データ比較中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    # コマンドライン引数からラウンドIDを取得
    round_id = None
    if len(sys.argv) > 1:
        try:
            round_id = int(sys.argv[1])
        except ValueError:
            print("無効なラウンドIDです。整数を入力してください。")
            sys.exit(1)
    
    verify_supabase_data(round_id)