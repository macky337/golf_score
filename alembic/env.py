from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db import Base
from modules.models import Member, Round, Score, MatchHandicap

# このオブジェクトは、.ini ファイル内の値にアクセスするために使用されます。
config = context.config

# config.fileConfig は、Python ログ設定を解釈します。
fileConfig(config.config_file_name)

# モデルのメタデータをここに追加します。
target_metadata = Base.metadata

def run_migrations_offline():
    """オフラインモードでマイグレーションを実行します。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """オンラインモードでマイグレーションを実行します。"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

# オフラインモードかオンラインモードかを判定して、対応する関数を実行します。
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()