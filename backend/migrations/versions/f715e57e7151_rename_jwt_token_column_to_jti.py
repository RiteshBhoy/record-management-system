"""Rename JWT token column to JTI

Revision ID: f715e57e7151
Revises: 718155fa9c44
Create Date: 2026-07-11 05:59:55.408748

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f715e57e7151'
down_revision = '718155fa9c44'
branch_labels = None
depends_on = None
def upgrade():
    """Rename the JWT token column to JTI and create its index."""

    with op.batch_alter_table(
        "token_manager",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "jwt_token",
            existing_type=sa.Text(),
            type_=sa.String(length=36),
            existing_nullable=False,
            new_column_name="jti",
        )

    op.create_index(
        "ix_token_manager_jti",
        "token_manager",
        ["jti"],
        unique=False,
    )


def downgrade():
    """Restore the original JWT token column name."""

    op.drop_index(
        "ix_token_manager_jti",
        table_name="token_manager",
    )

    with op.batch_alter_table(
        "token_manager",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "jti",
            existing_type=sa.String(length=36),
            type_=sa.Text(),
            existing_nullable=False,
            new_column_name="jwt_token",
        )