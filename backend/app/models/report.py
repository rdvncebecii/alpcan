from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.study import Study


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    study_id: Mapped[str] = mapped_column(ForeignKey("studies.id"), unique=True)

    # Lung-RADS
    overall_lung_rads: Mapped[str] = mapped_column(String(5))
    lung_rads_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # CXR Ensemble (if CXR pipeline)
    cxr_ensemble_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cxr_model_votes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # {"ark": true, "torchxray": false, "xraydar": true, "medrax": true}
    cxr_recommendation: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Report text (Llama-3 generated)
    summary_tr: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation_tr: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_report_tr: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Export paths
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dicom_sr_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fhir_document_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Processing info
    total_processing_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    agent_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    study: Mapped["Study"] = relationship(back_populates="report")
