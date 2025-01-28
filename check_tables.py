from sqlalchemy import inspect
from modules.db import engine

def check_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("存在するテーブル:", tables)

if __name__ == "__main__":
    check_tables()