"""upgrade_metrics_index_type

Revision ID: 625ad9a0b291
Revises: 78af24b0bab1
Create Date: 2026-06-30 13:58:26.353438

"""

# revision identifiers, used by Alembic.
revision = '625ad9a0b291'
down_revision = '78af24b0bab1'

from alembic import op
import sqlalchemy as sa

def upgrade():
    #We do all this because altering the column in place is both slow and a blocking task. Creating the new column and then swapping names 
    #allows users to continue accessing the table during the migration.
    op.execute('ALTER TABLE metrics ADD COLUMN big_id BIGINT;')
    op.execute('CREATE OR REPLACE FUNCTION set_new_id() RETURNS TRIGGER AS\n'\
                   '$BODY$\n'\
                   'BEGIN\n'\
                   '\t NEW.big_id := NEW.id;\n'\
                   '\t RETURN NEW;\n'\
                   'END\n'\
                   '$BODY$ LANGUAGE PLPGSQL;\n'\
                   'CREATE TRIGGER set_new_id_trigger BEFORE INSERT OR UPDATE ON {}\n'\
                   'FOR EACH ROW EXECUTE PROCEDURE set_new_id();\n'.format('metrics'))
    op.execute('UPDATE metrics SET big_id=id')
    op.execute('CREATE UNIQUE INDEX IF NOT EXISTS big_id_unique ON metrics(big_id);')
    op.execute('ALTER TABLE metrics ADD CONSTRAINT big_id_not_null CHECK (big_id IS NOT NULL) NOT VALID;')
    op.execute('ALTER TABLE metrics VALIDATE CONSTRAINT big_id_not_null;')
    op.execute('ALTER TABLE metrics DROP CONSTRAINT metrics_pkey, ADD CONSTRAINT metrics_pkey PRIMARY KEY USING INDEX big_id_unique;')
    op.execute('ALTER SEQUENCE metrics_id_seq OWNED BY metrics.big_id;')
    op.execute("ALTER TABLE metrics ALTER COLUMN big_id SET DEFAULT nextval('metrics_id_seq');")
    op.execute("ALTER TABLE metrics RENAME COLUMN id TO old_id;")
    op.execute("ALTER TABLE metrics RENAME COLUMN big_id TO id;")
    op.drop_column('metrics', 'old_id')
    op.execute('ALTER SEQUENCE metrics_id_seq as bigint MAXVALUE 9223372036854775807')
    op.execute('DROP TRIGGER IF EXISTS set_new_id_trigger ON metrics')
    # ### end Alembic commands ###


def downgrade():
    #This exists for completeness but know that performing this downgrade will necessarily delete data for records with IDs larger than MAXINT.
    op.add_column('metrics', sa.Column('small_id', sa.Integer(), unique=True))
    op.execute('DELETE FROM metrics WHERE id > 2147483647')
    op.execute('UPDATE metrics SET small_id=id')
    op.alter_column('metrics', 'small_id', nullable=False)
    op.drop_constraint('metrics_pkey', 'metrics', type_='primary')
    op.create_primary_key("metrics_pkey", "metrics", ["small_id", ])
    op.execute('ALTER SEQUENCE metrics_id_seq OWNED BY metrics.small_id;')
    op.execute("ALTER TABLE metrics ALTER COLUMN small_id SET DEFAULT nextval('metrics_id_seq');")
    op.alter_column('metrics', 'id', nullable=False, new_column_name='old_id')
    op.alter_column('metrics', 'small_id', nullable=False, new_column_name='id')
    op.drop_column('metrics', 'old_id')
    op.execute('ALTER SEQUENCE metrics_id_seq as int MAXVALUE 2147483647')