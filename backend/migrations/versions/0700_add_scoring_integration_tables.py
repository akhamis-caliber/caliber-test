"""Add scoring integration tables

Revision ID: 0700
Revises: 0691cd695bbc
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0700'
down_revision = '0691cd695bbc'
branch_labels = None
depends_on = None


def upgrade():
    # Create scoring_jobs table
    op.create_table('scoring_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('queued', 'processing', 'completed', 'failed', name='reportstatus'), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('progress', sa.Float(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for scoring_jobs
    op.create_index('idx_scoring_jobs_report_id', 'scoring_jobs', ['report_id'])
    op.create_index('idx_scoring_jobs_campaign_id', 'scoring_jobs', ['campaign_id'])
    op.create_index('idx_scoring_jobs_status', 'scoring_jobs', ['status'])
    op.create_index('idx_scoring_jobs_created_at', 'scoring_jobs', ['created_at'])

    # Create scoring_metrics table
    op.create_table('scoring_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=255), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('min_value', sa.Float(), nullable=True),
        sa.Column('max_value', sa.Float(), nullable=True),
        sa.Column('normalization_method', sa.String(length=50), nullable=True),
        sa.Column('outlier_method', sa.String(length=50), nullable=True),
        sa.Column('outlier_action', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for scoring_metrics
    op.create_index('idx_scoring_metrics_campaign_id', 'scoring_metrics', ['campaign_id'])
    op.create_index('idx_scoring_metrics_name', 'scoring_metrics', ['metric_name'])
    op.create_index('idx_scoring_metrics_active', 'scoring_metrics', ['is_active'])

    # Create scoring_history table
    op.create_table('scoring_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('scoring_job_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('config_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('results_summary', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('performance_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scoring_job_id'], ['scoring_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for scoring_history
    op.create_index('idx_scoring_history_campaign_id', 'scoring_history', ['campaign_id'])
    op.create_index('idx_scoring_history_report_id', 'scoring_history', ['report_id'])
    op.create_index('idx_scoring_history_created_at', 'scoring_history', ['created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_scoring_history_created_at', table_name='scoring_history')
    op.drop_index('idx_scoring_history_report_id', table_name='scoring_history')
    op.drop_index('idx_scoring_history_campaign_id', table_name='scoring_history')
    op.drop_index('idx_scoring_metrics_active', table_name='scoring_metrics')
    op.drop_index('idx_scoring_metrics_name', table_name='scoring_metrics')
    op.drop_index('idx_scoring_metrics_campaign_id', table_name='scoring_metrics')
    op.drop_index('idx_scoring_jobs_created_at', table_name='scoring_jobs')
    op.drop_index('idx_scoring_jobs_status', table_name='scoring_jobs')
    op.drop_index('idx_scoring_jobs_campaign_id', table_name='scoring_jobs')
    op.drop_index('idx_scoring_jobs_report_id', table_name='scoring_jobs')
    
    # Drop tables
    op.drop_table('scoring_history')
    op.drop_table('scoring_metrics')
    op.drop_table('scoring_jobs') 