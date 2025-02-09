"""Add match_front to Score

Revision ID: 8001400e25e2
Revises: bef81e194e19
Create Date: 2025-02-09 09:45:27.586348

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8001400e25e2'
down_revision: Union[str, None] = 'bef81e194e19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Score テーブルに match_front カラムを追加する操作ですが、
    # すでにこのカラムが存在している場合は重複追加エラーとなるため、ここは削除します。
    # with op.batch_alter_table('score') as batch_op:
    #     batch_op.add_column(sa.Column('match_front', sa.Integer(), nullable=True))
    
    # handicap_match テーブルへの変更について、SQLite の制約 ALTER 操作は
    # batch_alter_table を用いても制約名が指定されていないと動作しませんので、
    # ここでの制約 DROP/CREATE 操作は削除またはコメントアウトします。
    #
    # op.drop_constraint(None, 'handicap_match', type_='foreignkey')
    # op.drop_constraint(None, 'handicap_match', type_='foreignkey')
    # op.drop_constraint(None, 'handicap_match', type_='foreignkey')
    # op.create_foreign_key(None, 'handicap_match', 'member', ['player_2_id'], ['member_id'])
    # op.create_foreign_key(None, 'handicap_match', 'round', ['round_id'], ['round_id'])
    # op.create_foreign_key(None, 'handicap_match', 'member', ['player_1_id'], ['member_id'])
    # op.drop_column('handicap_match', 'match_id')
    
    # handicap_match テーブルの id カラム追加と total_only カラム追加はそのまま実行
    op.add_column('handicap_match', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, server_default='0'))
    op.add_column('handicap_match', sa.Column('total_only', sa.Boolean(), nullable=True))
    with op.batch_alter_table('handicap_match') as batch_op:
        batch_op.alter_column('id', server_default=None)

def downgrade() -> None:
    # downgrade でも不要な操作は削除します。
    op.add_column('handicap_match', sa.Column('match_id', sa.INTEGER(), nullable=False))
    # 以下の制約操作は削除
    # op.drop_constraint(None, 'handicap_match', type_='foreignkey')
    # op.drop_constraint(None, 'handicap_match', type_='foreignkey')
    # op.drop_constraint(None, 'handicap_match', type_='foreignkey')
    # op.create_foreign_key(None, 'handicap_match', 'members', ['player_1_id'], ['member_id'])
    # op.create_foreign_key(None, 'handicap_match', 'rounds', ['round_id'], ['round_id'])
    # op.create_foreign_key(None, 'handicap_match', 'members', ['player_2_id'], ['member_id'])
    op.drop_column('handicap_match', 'total_only')
    op.drop_column('handicap_match', 'id')
    with op.batch_alter_table('score') as batch_op:
        batch_op.drop_column('match_front')
