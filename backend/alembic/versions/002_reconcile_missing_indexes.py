"""Reconcile missing model indexes

Revision ID: 002_reconcile_missing_indexes
Revises: 001_initial_schema
Create Date: 2026-09-20 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_reconcile_missing_indexes'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_index(op.f('ix_document_relationships_parent_document_id'), 'document_relationships', ['parent_document_id'], unique=False)
    op.create_index(op.f('ix_document_relationships_related_document_id'), 'document_relationships', ['related_document_id'], unique=False)
    op.create_index(op.f('ix_extraction_warnings_question_id'), 'extraction_warnings', ['question_id'], unique=False)
    op.create_index(op.f('ix_review_items_question_id'), 'review_items', ['question_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_review_items_question_id'), table_name='review_items')
    op.drop_index(op.f('ix_extraction_warnings_question_id'), table_name='extraction_warnings')
    op.drop_index(op.f('ix_document_relationships_related_document_id'), table_name='document_relationships')
    op.drop_index(op.f('ix_document_relationships_parent_document_id'), table_name='document_relationships')
