from sqlalchemy import inspect, text
from modules.db import engine

def check_all_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("存在するテーブル:", tables)
    with engine.connect() as conn:
        for table in tables:
            print(f"--- テーブル: {table} ---")
            result = conn.execute(text(f"SELECT * FROM {table}"))
            rows = result.fetchall()
            for row in rows:
                print(row)
            print()

if __name__ == "__main__":
    check_all_tables()