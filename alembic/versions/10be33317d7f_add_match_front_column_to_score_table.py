"""Add match_front column to score table

Revision ID: 10be33317d7f
Revises: 8001400e25e2
Create Date: 2025-02-09 10:19:56.150281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10be33317d7f'
down_revision: Union[str, None] = '8001400e25e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite の Inspector を利用して、'score' テーブルのカラム一覧を取得
    conn = op.get_bind()
    inspector = sa.engine.reflection.Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('score')]
    
    if 'match_front' not in columns:
        with op.batch_alter_table('score') as batch_op:
            batch_op.add_column(sa.Column('match_front', sa.Integer(), nullable=True))
    
    # 以下、handicap_match テーブルへの変更など必要な操作を記述
    op.add_column('handicap_match', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, server_default='0'))
    op.add_column('handicap_match', sa.Column('total_only', sa.Boolean(), nullable=True))
    # ここから先の制約操作も SQLite では ALTER が難しいため、不要な操作は削除または調整してください。
    # ※ここでは、既存の操作が不要と判断した場合は削除する例とします。
    # op.drop_constraint(...), op.create_foreign_key(...), op.drop_column('handicap_match', 'match_id'), etc.
    with op.batch_alter_table('handicap_match') as batch_op:
        batch_op.alter_column('id', server_default=None)

def downgrade() -> None:
    with op.batch_alter_table('score') as batch_op:
        batch_op.drop_column('match_front')
