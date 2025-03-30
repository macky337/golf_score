#!/usr/bin/env python3
"""
バックアップからゲームポイントをリストアするスクリプト
"""

import os
import sys
import json
from datetime import datetime

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.supabase_client import get_supabase_client

def main():
    """バックアップからゲームポイント情報をリストアするスクリプト"""
    print("===== ゲームポイント復元ツール =====")
    
    # バックアップファイルパス
    backup_path = r"C:\Users\user\Documents\GitHub\golf_score\backups\remote_main_backup_20250225_140525.json"
    
    # バックアップファイルの存在確認
    if not os.path.exists(backup_path):
        print(f"エラー: バックアップファイル '{backup_path}' が見つかりません")
        return
    
    print(f"バックアップファイル '{backup_path}' を読み込み中...")
    
    try:
        # バックアップファイルからデータ読み込み
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # バックアップファイルの構造を分析
        print("バックアップファイル構造を分析中...")
        if isinstance(backup_data, dict):
            # トップレベルのキーを確認
            top_keys = list(backup_data.keys())
            print(f"バックアップには次のセクションが含まれています: {top_keys}")
            
            # スコアデータの可能なキー名のリスト
            possible_score_keys = ['score', 'scores', 'scoreData', 'score_data']
            
            # スコアデータを検索
            score_data = None
            score_key = None
            
            for key in possible_score_keys:
                if key in backup_data:
                    score_data = backup_data[key]
                    score_key = key
                    break
            
            # スコアデータが見つからない場合、トップレベルのすべてのキーを調査
            if score_data is None:
                for key, value in backup_data.items():
                    if isinstance(value, list) and len(value) > 0:
                        # 最初のアイテムにスコア関連のキーがあるか確認
                        first_item = value[0]
                        if isinstance(first_item, dict) and any(k in first_item for k in ['score_id', 'round_id', 'front_score', 'back_score']):
                            score_data = value
                            score_key = key
                            print(f"スコアデータが '{key}' キーの下に見つかりました")
                            break
            
            if score_data is None:
                # ファイルの完全な内容を表示（最初の100文字だけ）
                print("\nバックアップファイルの内容一部:")
                file_content = json.dumps(backup_data)[:100] + "..."
                print(file_content)
                
                print("\nエラー: バックアップからスコアデータを特定できませんでした。")
                print("バックアップファイルを手動で確認して、キー名を指定してください。")
                
                # 手動でキーを入力させる
                manual_key = input("スコアデータのキー名を入力してください (キャンセルする場合は Enter): ")
                if not manual_key:
                    return
                
                if manual_key in backup_data:
                    score_data = backup_data[manual_key]
                    score_key = manual_key
                else:
                    print(f"指定されたキー '{manual_key}' がバックアップに存在しません。")
                    return
                
        elif isinstance(backup_data, list):
            # リスト形式のバックアップ
            print("バックアップはリスト形式です。最初の数件を確認します...")
            # 最初の数アイテムを表示
            sample_items = backup_data[:3] if len(backup_data) >= 3 else backup_data
            for item in sample_items:
                print(f"サンプルアイテム: {json.dumps(item)[:100]}...")
            
            # スコアデータと思われる場合
            if len(backup_data) > 0 and isinstance(backup_data[0], dict) and any(k in backup_data[0] for k in ['score_id', 'round_id']):
                score_data = backup_data
                score_key = "root_list"
                print("バックアップ全体がスコアデータのリストと判断されました")
            else:
                print("エラー: バックアップデータの構造がサポートされていません。")
                return
        else:
            print("エラー: バックアップデータの形式が不正です")
            return
        
        if not score_data:
            print("エラー: バックアップにスコアデータが含まれていません")
            return
        
        if not isinstance(score_data, list):
            print(f"エラー: '{score_key}' の値がリスト形式ではありません")
            return
        
        print(f"バックアップから {len(score_data)} 件のスコアレコードを読み込みました")
        
        # Supabaseクライアント初期化
        supabase = get_supabase_client()
        
        # リストア対象のラウンド一覧を取得
        round_ids = set()
        for item in score_data:
            if isinstance(item, dict) and 'round_id' in item:
                round_ids.add(item['round_id'])
        
        if not round_ids:
            print("バックアップからラウンドIDが見つかりません。")
            return
        
        print(f"バックアップにはラウンドID {sorted(round_ids)} のデータが含まれています")
        
        # リストア対象のラウンドを選択
        selected_round_ids = select_rounds_to_restore(supabase, round_ids)
        if not selected_round_ids:
            print("リストア対象のラウンドが選択されませんでした。処理を中止します")
            return
        
        # データリストア処理
        print(f"\n選択された {len(selected_round_ids)} ラウンドのゲームポイントを復元します...")
        restore_stats = restore_game_points(supabase, score_data, selected_round_ids)
        
        # リストア統計表示
        print("\n===== 復元結果サマリー =====")
        print(f"処理したラウンド: {len(restore_stats['processed_rounds'])}")
        print(f"更新したスコア数: {restore_stats['updated_records']}")
        print(f"エラー件数: {restore_stats['errors']}")
        
        if restore_stats['skipped_records'] > 0:
            print(f"スキップしたレコード: {restore_stats['skipped_records']} (バックアップと現在の値が一致)")
        
        print("\n処理が完了しました")
        
    except json.JSONDecodeError:
        print("エラー: バックアップファイルのJSON解析に失敗しました")
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        print(traceback.format_exc())

def select_rounds_to_restore(supabase, round_ids):
    """リストア対象のラウンドを選択"""
    # ラウンド情報を取得
    round_info = {}
    for round_id in round_ids:
        try:
            round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
            if round_result.data:
                round_info[round_id] = round_result.data[0]
        except Exception as e:
            print(f"ラウンドID {round_id} の情報取得に失敗: {e}")
    
    # ラウンド選択メニュー表示
    print("\nリストア対象のラウンドを選択してください:")
    print("0: すべてのラウンド")
    
    sorted_round_ids = sorted(round_info.keys())
    for i, round_id in enumerate(sorted_round_ids):
        info = round_info.get(round_id, {})
        date = info.get('date_played', '不明')
        course = info.get('course_name', '不明')
        print(f"{i+1}: ID:{round_id} - {date} {course}")
    
    # 選択入力受付
    choice = input("\n数字を入力してください (複数選択はカンマ区切り、例: 1,3,4): ")
    
    if choice == "0":
        return sorted_round_ids
    
    selected_indices = []
    try:
        # カンマ区切りの入力を処理
        for part in choice.split(','):
            if part.strip():
                index = int(part.strip()) - 1
                if 0 <= index < len(sorted_round_ids):
                    selected_indices.append(index)
                else:
                    print(f"警告: {index+1} は有効な選択肢ではありません")
    except ValueError:
        print("無効な入力です。処理を中止します")
        return []
    
    if not selected_indices:
        print("有効なラウンドが選択されませんでした")
        return []
    
    selected_round_ids = [sorted_round_ids[i] for i in selected_indices]
    return selected_round_ids

def restore_game_points(supabase, score_data, round_ids):
    """選択されたラウンドのゲームポイントをリストア"""
    stats = {
        "processed_rounds": set(),
        "updated_records": 0,
        "skipped_records": 0,
        "errors": 0
    }
    
    # 各ラウンドごとに処理
    for round_id in round_ids:
        print(f"\n--- ラウンドID {round_id} の処理 ---")
        
        # 現在のスコアデータを取得
        try:
            current_scores_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
            current_scores = {s['member_id']: s for s in current_scores_result.data} if current_scores_result.data else {}
            
            if not current_scores:
                print(f"現在のデータベースにラウンドID {round_id} のスコアデータが見つかりません")
                continue
            
            # バックアップからスコアデータを抽出
            backup_scores = [s for s in score_data if s.get('round_id') == round_id]
            
            if not backup_scores:
                print(f"バックアップにラウンドID {round_id} のデータが見つかりません")
                continue
            
            # バックアップデータに基づいて更新
            for backup_score in backup_scores:
                member_id = backup_score.get('member_id')
                if member_id in current_scores:
                    current = current_scores[member_id]
                    
                    # 更新するフィールド
                    update_data = {}
                    
                    # front_game_pt, back_game_pt, extra_game_ptをチェック・更新
                    if 'front_game_pt' in backup_score and backup_score['front_game_pt'] != current.get('front_game_pt'):
                        update_data['front_game_pt'] = backup_score['front_game_pt']
                    
                    if 'back_game_pt' in backup_score and backup_score['back_game_pt'] != current.get('back_game_pt'):
                        update_data['back_game_pt'] = backup_score['back_game_pt']
                    
                    if 'extra_game_pt' in backup_score and backup_score['extra_game_pt'] != current.get('extra_game_pt'):
                        update_data['extra_game_pt'] = backup_score['extra_game_pt']
                    
                    # 更新が必要な場合
                    if update_data:
                        try:
                            print(f"メンバーID {member_id} のゲームポイントを更新します: {update_data}")
                            supabase.table('score').update(update_data).eq('score_id', current['score_id']).execute()
                            stats["updated_records"] += 1
                        except Exception as e:
                            print(f"更新エラー (メンバー {member_id}): {e}")
                            stats["errors"] += 1
                    else:
                        print(f"メンバーID {member_id} のゲームポイントは一致しています。更新不要")
                        stats["skipped_records"] += 1
                else:
                    print(f"メンバーID {member_id} は現在のデータに存在しません")
            
            stats["processed_rounds"].add(round_id)
            
        except Exception as e:
            print(f"ラウンドID {round_id} の処理中にエラー発生: {e}")
            stats["errors"] += 1
    
    return stats

if __name__ == "__main__":
    main()