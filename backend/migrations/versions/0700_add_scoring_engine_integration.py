"""Add scoring engine integration

Revision ID: 0700
Revises: 0691cd695bbc
Create Date: 2024-01-01 12:00:00.000000

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
    # Ensure all scoring-related tables exist and have proper indexes
    
    # Create scoring_jobs table if it doesn't exist
    op.create_table(
        'scoring_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('queued', 'processing', 'completed', 'failed', name='reportstatus'), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('progress', sa.Float(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create scoring_results table if it doesn't exist
    op.create_table(
        'scoring_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=255), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=True),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('weighted_score', sa.Float(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('metric_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create scoring_history table if it doesn't exist
    op.create_table(
        'scoring_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('scoring_job_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('config_snapshot', sa.JSON(), nullable=True),
        sa.Column('results_summary', sa.JSON(), nullable=True),
        sa.Column('performance_metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ),
        sa.ForeignKeyConstraint(['scoring_job_id'], ['scoring_jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create scoring_metrics table if it doesn't exist
    op.create_table(
        'scoring_metrics',
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
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('idx_scoring_jobs_report_id', 'scoring_jobs', ['report_id'])
    op.create_index('idx_scoring_jobs_campaign_id', 'scoring_jobs', ['campaign_id'])
    op.create_index('idx_scoring_jobs_status', 'scoring_jobs', ['status'])
    op.create_index('idx_scoring_jobs_created_at', 'scoring_jobs', ['created_at'])
    
    op.create_index('idx_scoring_results_report_id', 'scoring_results', ['report_id'])
    op.create_index('idx_scoring_results_metric_name', 'scoring_results', ['metric_name'])
    op.create_index('idx_scoring_results_score', 'scoring_results', ['score'])
    op.create_index('idx_scoring_results_created_at', 'scoring_results', ['created_at'])
    op.create_index('idx_scoring_results_report_metric', 'scoring_results', ['report_id', 'metric_name'])
    
    op.create_index('idx_scoring_history_campaign_id', 'scoring_history', ['campaign_id'])
    op.create_index('idx_scoring_history_report_id', 'scoring_history', ['report_id'])
    op.create_index('idx_scoring_history_created_at', 'scoring_history', ['created_at'])
    
    op.create_index('idx_scoring_metrics_campaign_id', 'scoring_metrics', ['campaign_id'])
    op.create_index('idx_scoring_metrics_name', 'scoring_metrics', ['metric_name'])
    op.create_index('idx_scoring_metrics_active', 'scoring_metrics', ['is_active'])
    
    # Add any missing columns to existing tables
    # Check if score_data column exists in reports table
    try:
        op.add_column('reports', sa.Column('score_data', sa.JSON(), nullable=True))
    except:
        pass  # Column already exists
    
    # Check if report_metadata column exists in reports table
    try:
        op.add_column('reports', sa.Column('report_metadata', sa.JSON(), nullable=True))
    except:
        pass  # Column already exists


def downgrade():
    # Remove indexes
    op.drop_index('idx_scoring_metrics_active', table_name='scoring_metrics')
    op.drop_index('idx_scoring_metrics_name', table_name='scoring_metrics')
    op.drop_index('idx_scoring_metrics_campaign_id', table_name='scoring_metrics')
    
    op.drop_index('idx_scoring_history_created_at', table_name='scoring_history')
    op.drop_index('idx_scoring_history_report_id', table_name='scoring_history')
    op.drop_index('idx_scoring_history_campaign_id', table_name='scoring_history')
    
    op.drop_index('idx_scoring_results_report_metric', table_name='scoring_results')
    op.drop_index('idx_scoring_results_created_at', table_name='scoring_results')
    op.drop_index('idx_scoring_results_score', table_name='scoring_results')
    op.drop_index('idx_scoring_results_metric_name', table_name='scoring_results')
    op.drop_index('idx_scoring_results_report_id', table_name='scoring_results')
    
    op.drop_index('idx_scoring_jobs_created_at', table_name='scoring_jobs')
    op.drop_index('idx_scoring_jobs_status', table_name='scoring_jobs')
    op.drop_index('idx_scoring_jobs_campaign_id', table_name='scoring_jobs')
    op.drop_index('idx_scoring_jobs_report_id', table_name='scoring_jobs')
    
    # Drop tables
    op.drop_table('scoring_metrics')
    op.drop_table('scoring_history')
    op.drop_table('scoring_results')
    op.drop_table('scoring_jobs') 