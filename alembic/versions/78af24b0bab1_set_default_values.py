"""set default values

Revision ID: 78af24b0bab1
Revises: 4b6faa5a296b
Create Date: 2017-11-15 15:46:44.253567

"""

# revision identifiers, used by Alembic.
revision = '78af24b0bab1'
down_revision = '4b6faa5a296b'

from alembic import op
from sqlalchemy import false
import sqlalchemy as sa


def upgrade():
    op.alter_column('metrics', 'author_num', server_default=sa.text("1::integer"))
    op.alter_column('metrics', 'citation_num', server_default=sa.text("0::integer"))
    op.alter_column('metrics', 'reference_num', server_default=sa.text("0::integer"))
    op.alter_column('metrics', 'refereed_citation_num', server_default=sa.text("0::integer"))
    op.alter_column('metrics', 'refereed', server_default=false())
    op.execute("ALTER TABLE metrics ALTER COLUMN citations SET DEFAULT array[]::varchar[];")
    op.execute("ALTER TABLE metrics ALTER COLUMN refereed_citations SET DEFAULT array[]::varchar[];")
    op.execute("ALTER TABLE metrics ALTER COLUMN downloads SET DEFAULT array[]::integer[];")
    op.execute("ALTER TABLE metrics ALTER COLUMN reads SET DEFAULT array[]::integer[];")

def downgrade():
    op.alter_column('metrics', 'author_num', server_default=None)
    op.alter_column('metrics', 'citation_num', server_default=None)
    op.alter_column('metrics', 'reference_num', server_default=None)
    op.alter_column('metrics', 'refereed_citation_num', server_default=None)
    op.alter_column('metrics', 'refereed', server_default=None)
    op.execute("ALTER TABLE metrics ALTER COLUMN citations DROP DEFAULT;")
    op.execute("ALTER TABLE metrics ALTER COLUMN refereed_citations DROP DEFAULT;")
    op.execute("ALTER TABLE metrics ALTER COLUMN downloads DROP DEFAULT;")
    op.execute("ALTER TABLE metrics ALTER COLUMN reads DROP DEFAULT;")
