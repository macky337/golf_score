from typing import Dict, List, Any, Optional
from modules.supabase_client import get_supabase_client
import streamlit as st
import time
import traceback

def save_round_results(round_id, player_data):
    """ラウンド結果をround_resultsテーブルに保存する"""
    supabase = get_supabase_client()
    
    print(f"ラウンドID {round_id} の結果を保存処理を開始します...")
    
    try:
        # 有効なメンバーIDのリスト取得
        member_result = supabase.table('member').select('member_id').execute()
        valid_member_ids = set([m['member_id'] for m in member_result.data])
        print(f"有効なメンバーID: {valid_member_ids}")
        
        # スコアテーブル確認（メンバーIDが存在するか）
        score_result = supabase.table('score').select('member_id').eq('round_id', round_id).execute()
        if not score_result.data:
            print(f"ラウンドID {round_id} のスコアデータが見つかりません")
        
        # 既存のround_resultsデータを取得
        existing_results = supabase.table('round_results').select('*').eq('round_id', round_id).execute()
        existing_count = len(existing_results.data) if existing_results.data else 0
        print(f"既存のround_resultsデータ: {existing_count} 件")
        
        # 既存データをメンバーIDでインデックス化
        existing_by_member = {r['member_id']: r for r in existing_results.data} if existing_results.data else {}
        
        # プレイヤーデータをsupabase形式に変換して保存
        records_to_upsert = []
        
        for member_id, data in player_data.items():
            if member_id not in valid_member_ids:
                continue  # 無効なメンバーIDはスキップ
            
            # PascalCase → snake_case に変換
            record = {
                'round_id': round_id,
                'member_id': member_id,
                'match_front': data.get('Match Front', 0),
                'match_back': data.get('Match Back', 0),
                'match_total': data.get('Match Total', 0),
                'match_extra': data.get('Match Extra', 0),
                'match_pt': data.get('Match Pt', 0),
                'putt_pt': data.get('Putt Pt', 0),
                'total_game_pt': data.get('Game Pt', 0),
                'total_pt': data.get('Total Pt', 0),  # この行が正しく処理されているか確認
            }
            
            # 既存レコードがある場合はID付与（更新用）
            if member_id in existing_by_member:
                record['id'] = existing_by_member[member_id]['id']
            
            records_to_upsert.append(record)
        
        # 保存処理
        if records_to_upsert:
            print(f"{len(records_to_upsert)}件のレコードをround_resultsテーブルに挿入します...")
            
            # デバッグ: 最初の1件の内容を表示
            if records_to_upsert:
                print(f"最初のレコード例: {records_to_upsert[0]}")
                print(f"Total Pt: {player_data[records_to_upsert[0]['member_id']].get('Total Pt')}")
            
            try:
                # 既存レコードの更新と新規レコードの挿入を一括で行う
                result = supabase.table('round_results').upsert(records_to_upsert).execute()
                print(f"保存完了: {len(result.data) if hasattr(result, 'data') and result.data else '不明'} 件")
                return True
            except Exception as e:
                print(f"レコード挿入中にエラーが発生しました: {e}")
                return False
        else:
            print("保存するレコードがありません")
            return False
    
    except Exception as e:
        print(f"ラウンドID {round_id} のデータ保存に一部失敗しました")
        print(f"エラー: {e}")
        return False

def get_round_results(round_id: int) -> dict:
    """
    指定されたラウンドIDのラウンド結果を取得する
    """
    supabase = get_supabase_client()
    try:
        response = supabase.table('round_results').select('*').eq('round_id', round_id).execute()
        results = {}
        if response.data:
            for record in response.data:
                results[record['member_id']] = {
                    'Match Front': record.get('match_front', 0),
                    'Match Back': record.get('match_back', 0),
                    'Match Total': record.get('match_total', 0),
                    'Match Extra': record.get('match_extra', 0),
                    'Match Pt': record.get('match_pt', 0),
                    'Putt Pt': record.get('putt_pt', 0),
                    'Game Pt': record.get('total_game_pt', 0),  # ここが正しく設定されているか確認
                    'Total Pt': record.get('total_pt', 0)       
                }
        return results
    except Exception as e:
        error_message = f"Error getting round results: {e}"
        print(error_message)
        try:
            st.error(error_message)
        except:
            pass  # Streamlitコンテキスト外での実行時にエラーを抑制
        return {}

def test_round_results():
    """round_resultsモジュールのテスト関数"""
    print("===== round_resultsモジュールテスト =====")
    
    try:
        # Supabaseクライアントを初期化
        supabase = get_supabase_client()
        
        # 最新ラウンドを取得
        latest_round = None
        print("最新のラウンドを取得中...")
        try:
            rounds_result = supabase.table('rounds').select('*').order('date_played', desc=True).limit(1).execute()
            if rounds_result.data:
                latest_round = rounds_result.data[0]
                print(f"テスト用ラウンドID: {latest_round['round_id']} ({latest_round['date_played']} - {latest_round['course_name']})")
            else:
                print("ラウンドデータがありません")
                return
        except Exception as e:
            print(f"ラウンド取得エラー: {e}")
            return
        
        # round_resultsデータを取得
        print("\nround_resultsデータを取得中...")
        round_results = get_round_results(latest_round['round_id'])
        
        if round_results:
            print(f"{len(round_results)}件のround_resultsデータが見つかりました")
            
            # round_resultsテーブルの構造を確認
            print("\nround_resultsのデータ構造:")
            for member_id, data in list(round_results.items())[:3]:  # 最初の3件のみ表示
                print(f"メンバーID: {member_id}")
                for key, value in data.items():
                    print(f"  {key}: {value}")
                print("  -----------")
        else:
            print("round_resultsデータが見つかりません")
        
        print("\n===== テスト完了 =====")
    
    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    # モジュールが直接実行された場合はテストを実行
    test_round_results()