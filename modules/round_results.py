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
    """ラウンド結果をround_resultsテーブルとscoreテーブルに保存"""
    try:
        client = get_supabase_client()
         # テーブルカラムの確認
        round_results_columns = get_table_columns('round_results')
        score_columns = get_table_columns('score')
        
        print(f"round_results カラム: {round_results_columns}")
        print(f"score カラム: {score_columns}")
        
        # まずround_resultsテーブルの既存データを削除（上書き）
        try:
            client.table('round_results').delete().eq('round_id', round_id).execute()
            print(f"既存のround_resultsデータを削除しました (round_id: {round_id})")
        except Exception as e:
            print(f"既存データの削除エラー（続行します）: {e}")
        
        # プレイヤーごとにデータを保存
        for player_id, data in player_data.items():
            try:                # round_resultsテーブルに保存するデータ
                # スキーマに合わせて正しいカラム名のみ使用
                match_pt = data.get('Match Pt', 0)
                putt_pt = data.get('Putt Pt', 0)
                game_pt = data.get('total_game_pt', data.get('Game Pt', 0))
                # total_ptは成分の合計として計算（データベーススキーマに依存しない）
                
                result_data = {
                    'round_id': round_id,
                    'member_id': player_id,  # メンバーIDを使用
                    'match_front': data.get('Match Front', 0),
                    'match_back': data.get('Match Back', 0),
                    'match_total': data.get('Match Total', 0),
                    'match_extra': data.get('Match Extra', 0),
                    'match_pt': match_pt,
                    'putt_pt': putt_pt,
                    'temp_game_pt': data.get('temp_game_pt', 0),
                    'total_game_pt': game_pt
                    # total_ptはround_resultsテーブルのスキーマに依存するため、存在する場合のみ追加
                }
                
                # total_ptカラムが存在するかは実際のスキーマ次第なので、
                # エラーが発生しないよう条件的に追加することも検討可能
                
                # データ挿入を試みる
                response = client.table('round_results').insert(result_data).execute()
                print(f"Round results saved for player {player_id}")
                
            except Exception as e:
                print(f"Error saving round results for player {player_id}: {e}")
            
            # scoreテーブルのデータを保存するために既存データを確認
            try:
                # 既存のスコアレコードを確認
                existing_score = client.table('score').select('score_id').eq('round_id', round_id).eq('member_id', player_id).execute()
                
                if existing_score.data:
                    # 既存のレコードがある場合、そのscore_idを使用
                    score_id = existing_score.data[0]['score_id']
                    print(f"既存のスコアレコードを更新します (ID: {score_id})")
                else:
                    # 既存のレコードがない場合、最大のscore_idを取得して新しいIDを生成
                    max_id_result = client.table('score').select('score_id').order('score_id', desc=True).limit(1).execute()
                    score_id = 1
                    if max_id_result.data:
                        score_id = max_id_result.data[0]['score_id'] + 1
                    print(f"新しいスコアレコードを作成します (ID: {score_id})")
                
                # スコアデータを作成（必ず'score_id'を含める）
                score_data = {
                    'score_id': score_id,  # 重要: scoreテーブルのプライマリキー
                    'round_id': round_id,
                    'member_id': player_id,
                    'front_score': data.get('Front Score', 0),
                    'back_score': data.get('Back Score', 0),
                    'extra_score': data.get('Extra Score', 0),
                    'front_game_pt': data.get('Front GP', 0),
                    'back_game_pt': data.get('Back GP', 0),
                    'extra_game_pt': data.get('Extra GP', 0),
                    'front_putt': data.get('Front Putt', data.get('Putt Front', 0)), 
                    'back_putt': data.get('Back Putt', data.get('Putt Back', 0)),
                    'extra_putt': data.get('Extra Putt', data.get('Putt Extra', 0)),
                    'total_score': data.get('Front Score', 0) + data.get('Back Score', 0)
                }
                
                # スコアの挿入または更新
                if existing_score.data:
                    # 既存のレコードを更新
                    score_response = client.table('score').update(score_data).eq('score_id', score_id).execute()
                else:
                    # 新しいレコードを挿入
                    score_response = client.table('score').insert(score_data).execute()
                
                print(f"Score data saved for player {player_id}")
                
            except Exception as score_e:
                print(f"Score data save error for player {player_id}: {score_e}")
        
        return True
    except Exception as e:
        print(f"Error saving round results: {e}")
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