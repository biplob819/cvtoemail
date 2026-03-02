"""Initial schema — all tables

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-03-02 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- cv_profiles ---
    op.create_table(
        'cv_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('personal_info', sa.JSON(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('work_experience', sa.JSON(), nullable=True),
        sa.Column('education', sa.JSON(), nullable=True),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('certifications', sa.JSON(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_cv_profiles_id'), 'cv_profiles', ['id'], unique=False)

    # --- app_settings ---
    op.create_table(
        'app_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_email', sa.String(), nullable=True),
        sa.Column('smtp_host', sa.String(), nullable=True),
        sa.Column('smtp_port', sa.Integer(), nullable=True),
        sa.Column('smtp_user', sa.String(), nullable=True),
        sa.Column('smtp_password', sa.String(), nullable=True),
        sa.Column('openai_api_key', sa.String(), nullable=True),
        sa.Column('openai_model', sa.String(), nullable=True),
        sa.Column('scan_frequency', sa.Integer(), nullable=True),
        sa.Column('scan_window_start', sa.Time(), nullable=True),
        sa.Column('scan_window_end', sa.Time(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- job_sources ---
    op.create_table(
        'job_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('portal_name', sa.String(), nullable=False),
        sa.Column('filters_description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_checked', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_job_sources_id'), 'job_sources', ['id'], unique=False)
    op.create_index(op.f('ix_job_sources_url'), 'job_sources', ['url'], unique=True)

    # --- jobs ---
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('company', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('is_new', sa.Boolean(), nullable=False),
        sa.Column(
            'discovered_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.Column('tailored_cv', sa.JSON(), nullable=True),
        sa.Column('cv_pdf_path', sa.String(), nullable=True),
        sa.Column('cv_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['job_sources.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_source_id'), 'jobs', ['source_id'], unique=False)
    op.create_index(op.f('ix_jobs_url'), 'jobs', ['url'], unique=True)

    # --- applications ---
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('cv_path', sa.String(), nullable=True),
        sa.Column('email_sent_to', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_applications_id'), 'applications', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_applications_id'), table_name='applications')
    op.drop_table('applications')

    op.drop_index(op.f('ix_jobs_url'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_source_id'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_id'), table_name='jobs')
    op.drop_table('jobs')

    op.drop_index(op.f('ix_job_sources_url'), table_name='job_sources')
    op.drop_index(op.f('ix_job_sources_id'), table_name='job_sources')
    op.drop_table('job_sources')

    op.drop_table('app_settings')

    op.drop_index(op.f('ix_cv_profiles_id'), table_name='cv_profiles')
    op.drop_table('cv_profiles')
