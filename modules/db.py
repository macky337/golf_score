from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.models import Base

# 例として SQLite を使用。実際の環境に合わせて DATABASE_URL を変更してください。
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# テーブルが存在しない場合は作成
Base.metadata.create_all(bind=engine)
