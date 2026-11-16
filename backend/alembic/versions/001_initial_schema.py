"""001_initial_schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-11-16 14:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Agents table (Document §4.1)
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('industry_category', sa.String(length=100), nullable=False),
        sa.Column('webhook_url', sa.Text(), nullable=False),
        sa.Column('interest_manifesto', sa.Text(), nullable=False),
        sa.Column('interest_embedding', Vector(1536), nullable=True),
        sa.Column('trust_score', sa.Float(), server_default='1.0', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    # HNSW Index for sub-15ms vector search (Document §4)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_agents_interest_embedding_hnsw "
        "ON agents USING hnsw (interest_embedding vector_cosine_ops);"
    )

    # 3. Posts table (Document §4.2)
    op.create_table(
        'posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('author_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('post_embedding', Vector(1536), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    # 4. Routing Logs table (Document §4.3)
    op.create_table(
        'routing_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vector_score', sa.Float(), nullable=False),
        sa.Column('rerank_score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='NOTIFIED', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    # 5. Comments table (Document §4.4)
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('comments')
    op.drop_table('routing_logs')
    op.drop_table('posts')
    op.drop_table('agents')
