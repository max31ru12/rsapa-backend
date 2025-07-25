"""answered field contact message

Revision ID: 005
Revises: 004
Create Date: 2025-07-20 18:55:43.336786

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "contact_messages", sa.Column("answered", sa.Boolean(), server_default=sa.text("false"), nullable=False)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("contact_messages", "answered")
    # ### end Alembic commands ###
