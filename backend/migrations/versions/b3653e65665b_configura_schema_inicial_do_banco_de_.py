"""Configura schema inicial do banco de dados com DrawingBoard e Stroke

Revision ID: b3653e65665b
Revises: 
Create Date: 2025-05-24 18:19:57.288653

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3653e65665b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('drawing_board',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('stroke',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('drawing_board_id', sa.Integer(), nullable=False),
    sa.Column('color', sa.String(length=7), nullable=False),
    sa.Column('line_width', sa.Float(), nullable=False),
    sa.Column('points_json', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['drawing_board_id'], ['drawing_board.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('stroke')
    op.drop_table('drawing_board')
    # ### end Alembic commands ###
