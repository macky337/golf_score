from typing import Dict, List, Any, Optional
from modules.supabase_client import get_supabase_client
import streamlit as st
import time
import traceback

def save_round_results(round_id: int, player_data: dict) -> bool:
    """
    プレイヤーの計算結果をround_resultsテーブルに保存する
    """
    supabase = get_supabase_client()
    try:
        print(f"ラウンドID {round_id} の結果を保存処理を開始します...")
        
        # memberテーブル（単数形）からメンバー情報を取得して存在確認
        try:
            members_response = supabase.table('member').select('member_id').execute()
            valid_member_ids = set(int(member['member_id']) for member in members_response.data)
            print(f"有効なメンバーID: {valid_member_ids}")
            
            if not valid_member_ids:
                print("memberテーブルにデータが存在しません。先にメンバー登録を行ってください。")
                try:
                    st.error("memberテーブルにデータが存在しません。先にメンバー登録を行ってください。")
                except:
                    pass
                return False
                
        except Exception as member_error:
            print(f"メンバーデータの取得中にエラーが発生しました: {member_error}")
            valid_member_ids = set()
        
        # スコアテーブルからデータを取得して、既存のスコアを更新する前に確認する
        try:
            print("scoreテーブルを確認中...")
            score_data = supabase.table('score').select('*').eq('round_id', round_id).execute()
            
            if score_data.data:
                print(f"ラウンドID {round_id} のスコアデータが {len(score_data.data)} 件見つかりました")
                # 最初のレコードからカラム名を取得
                available_columns = score_data.data[0].keys() if score_data.data else []
                print(f"利用可能なスコアカラム: {available_columns}")
                
                # スコアテーブルのIDをマップ（後で検索するため）
                score_id_map = {}
                for score in score_data.data:
                    member_id = score.get('member_id')
                    if member_id:
                        score_id_map[int(member_id)] = score.get('id')
                print(f"スコアID対応表: {score_id_map}")
            else:
                print(f"ラウンドID {round_id} のスコアデータが見つかりません")
                available_columns = []
                score_id_map = {}
        except Exception as score_error:
            print(f"スコアデータの取得中にエラーが発生しました: {score_error}")
            available_columns = []
            score_id_map = {}
        
        # 既存のround_resultsデータを取得
        try:
            existing_results = supabase.table('round_results').select('*').eq('round_id', round_id).execute()
            existing_data = {result['member_id']: result for result in existing_results.data} if existing_results.data else {}
            print(f"既存のround_resultsデータ: {len(existing_data)} 件")
        except Exception as e:
            existing_data = {}
            print(f"既存のround_resultsの取得中にエラー: {e}")
        
        # スコアの更新および結果データの保存の準備
        records_to_insert = []
        records_to_update = []
        score_updates = []
        
        # 各プレイヤーのデータを処理
        for member_id_raw, data in player_data.items():
            try:
                member_id = int(member_id_raw)
                
                if member_id in valid_member_ids:
                    # データの準備
                    result_record = {
                        'round_id': round_id,
                        'member_id': member_id,
                        'match_front': data.get('Match Front', 0),
                        'match_back': data.get('Match Back', 0),
                        'match_total': data.get('Match Total', 0),
                        'match_extra': data.get('Match Extra', 0),
                        'match_pt': data.get('Match Pt', 0),
                        'putt_pt': data.get('Putt Pt', 0),
                        'temp_game_pt': data.get('Game Pt', 0),
                        'total_game_pt': data.get('Total Pt', 0)
                    }
                    
                    # 既存データがあれば更新、なければ挿入
                    if member_id in existing_data:
                        result_record['id'] = existing_data[member_id]['id']
                        records_to_update.append(result_record)
                    else:
                        records_to_insert.append(result_record)
                    
                    # スコアテーブルも更新（利用可能なカラムがあれば）
                    if score_id_map.get(member_id) and available_columns:
                        score_update = {'id': score_id_map[member_id]}
                        
                        # 必要なカラムのみ更新
                        if 'total_pt' in available_columns:
                            score_update['total_pt'] = data.get('Total Pt', 0)
                        
                        if 'front_game_pt' in available_columns:
                            score_update['front_game_pt'] = data.get('Match Front', 0)
                        
                        if 'back_game_pt' in available_columns:
                            score_update['back_game_pt'] = data.get('Match Back', 0)
                        
                        if 'extra_game_pt' in available_columns:
                            score_update['extra_game_pt'] = data.get('Match Extra', 0)
                            
                        if score_update:
                            score_updates.append(score_update)
                else:
                    print(f"メンバーID {member_id} は有効なメンバーとして見つかりませんでした。スキップします。")
            except ValueError as ve:
                print(f"メンバーIDの変換中にエラーが発生しました ({member_id_raw}): {ve}")
        
        # メンバーIDが不正なためにレコードが0になった場合
        if not records_to_insert and not records_to_update:
            print("有効なメンバーIDが見つかりません。データを保存できません。")
            try:
                st.error("有効なメンバーIDが見つかりません。データを保存できません。")
            except:
                pass
            return False
        
        # round_resultsテーブルへの挿入・更新を実行
        success = True
        
        # 新規レコードの挿入
        if records_to_insert:
            try:
                print(f"{len(records_to_insert)}件のレコードをround_resultsテーブルに挿入します...")
                insert_response = supabase.table('round_results').insert(records_to_insert).execute()
                if not insert_response.data:
                    print("新規レコードの挿入に失敗しました")
                    success = False
                else:
                    print(f"新規レコード挿入成功: {len(insert_response.data)}件")
            except Exception as insert_error:
                print(f"レコード挿入中にエラーが発生しました: {insert_error}")
                success = False
        
        # 既存レコードの更新
        if records_to_update:
            try:
                print(f"{len(records_to_update)}件のレコードをround_resultsテーブルで更新します...")
                update_success_count = 0
                
                for record in records_to_update:
                    try:
                        record_id = record.pop('id')  # idを取り出して、更新データから除外
                        update_response = supabase.table('round_results').update(record).eq('id', record_id).execute()
                        if update_response.data:
                            update_success_count += 1
                    except Exception as e:
                        print(f"レコードID {record_id} の更新中にエラーが発生しました: {e}")
                
                print(f"既存レコード更新成功: {update_success_count}/{len(records_to_update)}件")
                if update_success_count != len(records_to_update):
                    success = False
            except Exception as update_error:
                print(f"レコード更新中にエラーが発生しました: {update_error}")
                success = False
        
        # スコアテーブルの更新
        if score_updates:
            try:
                print(f"{len(score_updates)}件のスコアレコードを更新します...")
                score_success_count = 0
                
                for score_update in score_updates:
                    try:
                        score_id = score_update.pop('id')  # idを取り出して、更新データから除外
                        update_response = supabase.table('score').update(score_update).eq('id', score_id).execute()
                        if update_response.data:
                            score_success_count += 1
                    except Exception as e:
                        print(f"スコアID {score_id} の更新中にエラーが発生しました: {e}")
                
                print(f"スコアレコード更新成功: {score_success_count}/{len(score_updates)}件")
            except Exception as score_update_error:
                print(f"スコア更新中にエラーが発生しました: {score_update_error}")
                # スコア更新の失敗は全体の成功判定には影響させない
        
        if success:
            print(f"ラウンドID {round_id} のデータ保存に成功しました")
            return True
        else:
            print(f"ラウンドID {round_id} のデータ保存に一部失敗しました")
            return False
                
    except Exception as e:
        error_details = traceback.format_exc()
        error_message = f"ラウンド結果の保存中にエラーが発生しました: {e}"
        print(error_message)
        print(f"エラー詳細: {error_details}")
        try:
            st.error(error_message)
        except:
            pass
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
                    'Game Pt': record.get('temp_game_pt', 0),
                    'Total Pt': record.get('total_game_pt', 0)
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