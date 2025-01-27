# scripts/init_db.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.db import engine
from modules.models import Base

def init_db():
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

if __name__ == "__main__": 
    init_db()
