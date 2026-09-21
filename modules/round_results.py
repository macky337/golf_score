from typing import Dict, List, Any, Optional
from modules.supabase_client import get_supabase_client
import streamlit as st
import time
import traceback
import os
from supabase import Client  # 型ヒント用のみ

# Supabase接続は get_supabase_client() を使用

def get_table_columns(table_name):
    """テーブルの実際のカラム名を取得する"""
    client = get_supabase_client()
    try:
        response = client.table(table_name).select('*').limit(1).execute()
        if response.data:
            return set(response.data[0].keys())
        else:
            print(f"警告: {table_name}テーブルにデータがないため、カラム情報を取得できません")
            # 一般的なカラム名を返す (予想されるカラム)
            if table_name == 'round_results':
                return {'id', 'round_id', 'member_id', 'match_front', 'match_back', 'match_total', 
                        'match_extra', 'match_pt', 'putt_pt', 'temp_game_pt', 'total_game_pt', 
                        'created_at', 'updated_at', 'total_pt'}
            elif table_name == 'score':
                return {'score_id', 'round_id', 'member_id', 'front_score', 'back_score', 'extra_score',
                        'front_putt', 'back_putt', 'extra_putt', 'front_game_pt', 'back_game_pt', 
                        'extra_game_pt', 'created_at'}
            return set()
    except Exception as e:
        print(f"スキーマ情報取得エラー ({table_name}): {e}")
        return set()

def save_round_results(round_id, player_data):
    """入力スコアを変更せず、計算結果だけを原子的に置き換える。"""
    from modules.round_persistence import save_calculation_atomic
    try:
        client = get_supabase_client()
        if client is None:
            return False
        save_calculation_atomic(client, round_id, player_data)
        return True
    except Exception as error:
        print(f"計算結果を保存できませんでした: {error}")
        return False

def get_round_results(round_id: int) -> dict:
    """
    指定されたラウンドIDのラウンド結果を取得する
    member_id昇順でソートされた結果を返す
    """
    from collections import OrderedDict
    
    client = get_supabase_client()
    try:
        # member_id順でソートして取得
        response = client.table('round_results').select('*').eq('round_id', round_id).order('member_id').execute()
        results = OrderedDict()
        
        # レスポンスデータの確認
        print(f"Round results response data: {response}")
        
        if response.data:
            # データはすでにmember_id昇順でソートされている
            for record in response.data:
                # スキーマにmember_idが存在することがわかったので、明示的に使用
                member_id = record.get('member_id')
                
                # member_idが取得できなかった場合はスキップ
                if member_id is None:
                    print(f"Warning: Could not find member_id in record: {record}")
                    continue
                  # Game Ptにはtotal_game_ptを使用（game_ptは存在しない）
                match_pt = record.get('match_pt', 0)
                putt_pt = record.get('putt_pt', 0)
                game_pt = record.get('total_game_pt', 0)
                total_pt = match_pt + putt_pt + game_pt  # total_ptを計算で算出
                
                results[member_id] = {
                    'Match Front': record.get('match_front', 0),
                    'Match Back': record.get('match_back', 0),
                    'Match Total': record.get('match_total', 0),
                    'Match Extra': record.get('match_extra', 0),
                    'Match Pt': match_pt,
                    'Putt Pt': putt_pt,
                    'Game Pt': game_pt,
                    'Total Pt': total_pt       
                }
        return results
    except Exception as e:
        error_message = f"Error getting round results: {e}"
        print(error_message)
        print(f"Exception details: {traceback.format_exc()}")
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
        client = get_supabase_client()
        
        # 最新ラウンドを取得
        latest_round = None
        print("最新のラウンドを取得中...")
        try:
            rounds_result = client.table('rounds').select('*').order('date_played', desc=True).limit(1).execute()
            
            # rounds テーブルのデータ構造を確認
            if rounds_result.data:
                print(f"Rounds table structure: {rounds_result.data[0].keys()}")
                latest_round = rounds_result.data[0]
                print(f"テスト用ラウンドID: {latest_round['round_id']} ({latest_round['date_played']} - {latest_round['course_name']})")
            else:
                print("ラウンドデータがありません")
                return
        except Exception as e:
            print(f"ラウンド取得エラー: {e}")
            return
        
        # round_results テーブルの列名を確認
        try:
            columns_info = client.table('round_results').select('*').limit(1).execute()
            if columns_info.data:
                print(f"Round_results table columns: {columns_info.data[0].keys()}")
            else:
                print("Round_results テーブルにデータがありません")
        except Exception as e:
            print(f"テーブル構造確認エラー: {e}")
        
        # round_resultsデータを取得
        print("\nround_resultsデータを取得中...")
        round_results = get_round_results(latest_round['round_id'])
        
        if round_results:
            print(f"{len(round_results)}件のround_resultsデータが見つかりました")
            
            # round_resultsテーブルの構造を確認
            print("\nround_resultsのデータ構造:")
            for player_id, data in list(round_results.items())[:3]:  # 最初の3件のみ表示
                print(f"プレイヤーID: {player_id}")
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
