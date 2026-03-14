"""Initial schema — patients, studies, nodules, reports.

Revision ID: 001
Revises:
Create Date: 2026-03-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # patients
    op.create_table(
        "patients",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("anonymous_id", sa.String(), unique=True, nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("sex", sa.String(1), nullable=True),
        sa.Column("smoking_status", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_patients_anonymous_id", "patients", ["anonymous_id"])

    # studies
    op.create_table(
        "studies",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("study_instance_uid", sa.String(), unique=True, nullable=False),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("modality", sa.String(10), nullable=False),
        sa.Column("study_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("series_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("instance_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("slice_thickness", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="uploaded"),
        sa.Column("pipeline_type", sa.String(10), nullable=True),
        sa.Column("overall_lung_rads", sa.String(5), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_studies_study_instance_uid", "studies", ["study_instance_uid"])

    # nodules
    op.create_table(
        "nodules",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("study_id", sa.String(), sa.ForeignKey("studies.id"), nullable=False),
        sa.Column("location_description", sa.String(200), nullable=True),
        sa.Column("coord_x", sa.Float(), nullable=True),
        sa.Column("coord_y", sa.Float(), nullable=True),
        sa.Column("coord_z", sa.Float(), nullable=True),
        sa.Column("diameter_mm", sa.Float(), nullable=False),
        sa.Column("volume_mm3", sa.Float(), nullable=True),
        sa.Column("density", sa.String(20), nullable=True),
        sa.Column("morphology", sa.String(50), nullable=True),
        sa.Column("malignancy_score", sa.Float(), nullable=True),
        sa.Column("detection_confidence", sa.Float(), nullable=True),
        sa.Column("lung_rads_category", sa.String(5), nullable=True),
        sa.Column("previous_diameter_mm", sa.Float(), nullable=True),
        sa.Column("volume_doubling_time_days", sa.Float(), nullable=True),
        sa.Column("growth_rate_percent", sa.Float(), nullable=True),
        sa.Column("heatmap_path", sa.String(500), nullable=True),
        sa.Column("agent_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # reports
    op.create_table(
        "reports",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("study_id", sa.String(), sa.ForeignKey("studies.id"), unique=True, nullable=False),
        sa.Column("overall_lung_rads", sa.String(5), nullable=False),
        sa.Column("lung_rads_details", sa.JSON(), nullable=True),
        sa.Column("cxr_ensemble_score", sa.Float(), nullable=True),
        sa.Column("cxr_model_votes", sa.JSON(), nullable=True),
        sa.Column("cxr_recommendation", sa.String(100), nullable=True),
        sa.Column("summary_tr", sa.Text(), nullable=True),
        sa.Column("recommendation_tr", sa.Text(), nullable=True),
        sa.Column("full_report_tr", sa.Text(), nullable=True),
        sa.Column("pdf_path", sa.String(500), nullable=True),
        sa.Column("dicom_sr_path", sa.String(500), nullable=True),
        sa.Column("fhir_document_id", sa.String(200), nullable=True),
        sa.Column("total_processing_seconds", sa.Float(), nullable=True),
        sa.Column("agent_results", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("nodules")
    op.drop_table("studies")
    op.drop_index("ix_patients_anonymous_id", table_name="patients")
    op.drop_table("patients")
