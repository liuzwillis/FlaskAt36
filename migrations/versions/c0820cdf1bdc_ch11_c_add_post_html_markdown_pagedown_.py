"""ch11-c add post-html markdown-pagedown and post-link

Revision ID: c0820cdf1bdc
Revises: 63a37928847b
Create Date: 2018-05-03 16:36:16.759414

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0820cdf1bdc'
down_revision = '63a37928847b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('body_html', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('posts', 'body_html')
    # ### end Alembic commands ###