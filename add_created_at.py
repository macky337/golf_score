from sqlalchemy import text, create_engine
import datetime

# データベースエンジンの直接作成
engine = create_engine('sqlite:///golf_app.db', echo=False)

def add_created_at_columns():
    with engine.connect() as conn:
        try:
            # トランザクション開始
            trans = conn.begin()
            
            # 各テーブルにcreated_atカラムを追加
            tables = ['member', 'rounds', 'score', 'handicap_match']
            current_time = datetime.datetime.now().isoformat()

            for table in tables:
                try:
                    # カラム追加
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN created_at TIMESTAMP"))
                    print(f"{table} テーブルに created_at カラムを追加しました")
                    
                    # 既存レコードの created_at を現在時刻で更新
                    conn.execute(
                        text(f"UPDATE {table} SET created_at = :timestamp"),
                        {"timestamp": current_time}
                    )
                    print(f"{table} テーブルの既存レコードを更新しました")
                
                except Exception as table_error:
                    print(f"{table} テーブルの処理中にエラーが発生しました: {str(table_error)}")
                    continue
            
            # トランザクションのコミット
            trans.commit()
            print("全てのテーブルの更新が完了しました")

        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
            # トランザクションのロールバック
            trans.rollback()
            raise

if __name__ == "__main__":
    add_created_at_columns()