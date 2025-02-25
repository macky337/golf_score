from supabase import create_client
import datetime
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import time
import json

# 環境変数の読み込み
load_dotenv()

# Supabase の設定
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# SQLite データベースの接続
sqlite_engine = create_engine('sqlite:///golf_app.db', echo=False)

def clean_data(data, table_name):
    """データをクリーンアップして適切な形式に変換する"""
    cleaned = {}
    
    for key, value in data.items():
        if value is None:
            continue
            
        if key == 'created_at':
            try:
                if isinstance(value, str):
                    cleaned[key] = datetime.datetime.fromisoformat(value)
                else:
                    cleaned[key] = value
            except ValueError:
                continue
                
        elif key in ['date', 'date_played'] and value:
            try:
                if isinstance(value, str):
                    cleaned[key] = datetime.datetime.fromisoformat(value).date().isoformat()
                elif isinstance(value, datetime.date):
                    cleaned[key] = value.isoformat()
            except ValueError:
                continue
                
        # スコアテーブルのゲームポイント関連のカラム名を修正
        elif table_name == 'score' and key in [
            'front_game_pt', 'back_game_pt', 'extra_game_pt',  # 元のカラム名
            'front_gp', 'back_gp', 'extra_gp',  # 新しいカラム名
            'match_pt', 'put_pt', 'total_pt'
        ]:
            # カラム名の変換マッピング
            column_mapping = {
                'front_game_pt': 'front_gp',
                'back_game_pt': 'back_gp',
                'extra_game_pt': 'extra_gp'
            }
            
            # キーを変換（必要な場合）
            transformed_key = column_mapping.get(key, key)
            cleaned[transformed_key] = float(value or 0)
            
        elif table_name == 'handicap_match' and key == 'total_only':
            cleaned[key] = bool(value)
            
        else:
            cleaned[key] = value
            
    return cleaned

def migrate_table(conn, table_name, select_query):
    """テーブルのデータを移行する汎用関数"""
    try:
        records = conn.execute(text(select_query)).fetchall()
        column_names = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        columns = [col[1] for col in column_names]

        for record in records:
            try:
                # レコードをディクショナリに変換
                data = dict(zip(columns, record))
                
                # データのクリーンアップと変換
                cleaned_data = clean_data(data, table_name)
                
                if not cleaned_data:
                    print(f"Warning: Empty data for {table_name} ID {record[0]}")
                    continue

                # デバッグ情報の出力
                if table_name == 'score':
                    print(f"Score data before migration: {data}")
                    print(f"Score data after cleaning: {cleaned_data}")

                # Supabase へのデータ送信
                result = supabase.table(table_name).upsert(cleaned_data).execute()
                print(f"{table_name} migrated: ID {record[0]}")
                
                time.sleep(0.1)  # レート制限を避けるため

            except Exception as record_error:
                print(f"Error processing {table_name} record {record[0]}")
                print(f"Original data: {json.dumps(data, default=str)}")
                print(f"Cleaned data: {json.dumps(cleaned_data, default=str)}")
                print(f"Error: {str(record_error)}")
                continue

    except Exception as e:
        print(f"Error migrating {table_name}: {str(e)}")
        raise

def migrate_data():
    try:
        with sqlite_engine.connect() as conn:
            # メンバーデータの移行
            migrate_table(conn, 'member', "SELECT * FROM member ORDER BY member_id")
            
            # ラウンドデータの移行
            migrate_table(conn, 'rounds', "SELECT * FROM rounds ORDER BY round_id")
            
            # スコアデータの移行
            migrate_table(conn, 'score', "SELECT * FROM score ORDER BY score_id")
            
            # ハンディキャップマッチデータの移行
            migrate_table(conn, 'handicap_match', "SELECT * FROM handicap_match ORDER BY id")

            print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_data()