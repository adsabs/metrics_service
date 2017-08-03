"""Created DB Structure

Revision ID: 4b6faa5a296b
Revises: None
Create Date: 2017-08-03 13:02:51.893908

"""

# revision identifiers, used by Alembic.
revision = '4b6faa5a296b'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Boolean, Integer, String, Column, DateTime
from sqlalchemy.dialects import postgresql

def upgrade():
    
    op.create_table('metrics',
        Column('id', Integer(), nullable=False),
        Column('bibcode', String(length=255), nullable=False, index=True),

        Column('an_citations', postgresql.REAL),
        Column('an_refereed_citations', postgresql.REAL),
        Column('author_num', Integer),
        Column('citations', postgresql.ARRAY(String)),
        Column('citation_num', Integer),
        Column('downloads', postgresql.ARRAY(Integer)),
        Column('reads', postgresql.ARRAY(Integer)),
        Column('refereed', Boolean),
        Column('refereed_citations', postgresql.ARRAY(String)),
        Column('refereed_citation_num', Integer),
        Column('reference_num', Integer),
        Column('rn_citations', postgresql.REAL),
        Column('rn_citation_data', postgresql.JSON),
        Column('modtime', DateTime),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bibcode')
    )
    
def downgrade():
    op.drop_table('metrics')
