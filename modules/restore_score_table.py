import json
import datetime
import os
import streamlit as st

from modules.supabase_client import get_supabase_client

def load_backup_data(filename):
    """指定されたバックアップファイルからデータを読み込む"""
    backup_dir = "backups"
    backup_path = os.path.join(backup_dir, filename)
    
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"バックアップファイル {filename} が見つかりません")
    
    with open(backup_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def merge_score_data(main_data, additional_data):
    """2つのバックアップデータからスコアデータをマージする"""
    # スコアデータを辞書に変換（キー：score_id）
    merged_scores = {}
    
    # 最初のデータセットを追加
    if 'scores' in main_data:
        for score in main_data['scores']:
            if 'score_id' in score:
                merged_scores[score['score_id']] = score
    
    # 2つ目のデータセットでマージ（存在するフィールドを更新・追加）
    if 'scores' in additional_data:
        for score in additional_data['scores']:
            if 'score_id' in score:
                score_id = score['score_id']
                if score_id in merged_scores:
                    # 既存のレコードに追加データをマージ
                    for key, value in score.items():
                        if key != 'score_id':  # score_idは上書きしない
                            merged_scores[score_id][key] = value
                else:
                    # 新しいレコードを追加
                    merged_scores[score_id] = score
    
    # 辞書からリストに戻す
    return list(merged_scores.values())

def restore_combined_score_table():
    """2つのバックアップファイルからスコアテーブルを復元する"""
    try:
        # バックアップファイル名
        main_backup = "golf_score_backup_20250225_140823.json"
        additional_backup = "remote_main_backup_20250225_140525.json"
        
        st.info(f"メインバックアップファイル: {main_backup}")
        st.info(f"追加バックアップファイル: {additional_backup}")
        
        # バックアップデータの読み込み
        main_data = load_backup_data(main_backup)
        additional_data = load_backup_data(additional_backup)
        
        # データのマージ
        st.info("2つのバックアップからデータをマージ中...")
        merged_scores = merge_score_data(main_data, additional_data)
        
        st.info(f"マージ後のスコアデータ: {len(merged_scores)}件")
        
        # Supabaseクライアント取得
        supabase = get_supabase_client()
        
        # スコアテーブルを一度クリア
        st.warning("スコアテーブルのデータを削除中...")
        supabase.table('score').delete().neq('id', -1).execute()
        
        # マージしたスコアデータの挿入
        st.info("スコアデータを復元中...")
        
        # バッチサイズを設定（一度に挿入するデータ数）
        batch_size = 50
        successful_inserts = 0
        failed_inserts = 0
        
        for i in range(0, len(merged_scores), batch_size):
            batch = merged_scores[i:i+batch_size]
            
            # バッチ挿入
            try:
                # データクリーニングと変換
                for score in batch:
                    # put_pt を putt_pt に修正（存在する場合）
                    if 'put_pt' in score and 'putt_pt' not in score:
                        score['putt_pt'] = score.pop('put_pt')
                    
                    # 必須フィールドが存在することを確認
                    required_fields = ['round_id', 'member_id', 'score_id']
                    missing_fields = [field for field in required_fields if field not in score]
                    
                    if missing_fields:
                        st.warning(f"スコアID {score.get('score_id', 'unknown')} に必須フィールドが不足しています: {', '.join(missing_fields)}")
                        failed_inserts += 1
                        continue
                
                # エラーにならなかったスコアのみを挿入
                valid_scores = [s for s in batch if all(field in s for field in required_fields)]
                if valid_scores:
                    supabase.table('score').insert(valid_scores).execute()
                    successful_inserts += len(valid_scores)
                
                st.info(f"進捗: {min(i+batch_size, len(merged_scores))}/{len(merged_scores)}件")
            except Exception as e:
                st.error(f"データ挿入中にエラーが発生しました (バッチ {i//batch_size + 1}): {str(e)}")
                if hasattr(e, 'details'):
                    st.error(f"エラーの詳細: {e.details}")
                failed_inserts += len(batch)
        
        st.success(f"スコアデータの復元が完了しました: 成功={successful_inserts}件, 失敗={failed_inserts}件")
        return True
        
    except Exception as e:
        st.error(f"リストア中にエラーが発生しました: {str(e)}")
        if hasattr(e, 'details'):
            st.error(f"エラーの詳細: {e.details}")
        return False

if __name__ == "__main__":
    restore_combined_score_table()
