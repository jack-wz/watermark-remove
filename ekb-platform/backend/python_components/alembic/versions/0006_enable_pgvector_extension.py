"""enable_pgvector_extension

Revision ID: 0006
Revises: 0005 
Create Date: 2024-08-27 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, None] = '0005' # Previous migration was for ingested_documents table
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def downgrade() -> None:
    # Downgrading might not be straightforward if data depends on the extension.
    # For now, we'll comment out the drop extension command, as it could lead to data loss
    # if there are tables using the vector type.
    # op.execute("DROP EXTENSION IF EXISTS vector;")
    pass # Or log a message indicating manual intervention might be needed.
