import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Study(Base):
    __tablename__ = "studies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    study_instance_uid: Mapped[str] = mapped_column(String, unique=True, index=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    modality: Mapped[str] = mapped_column(String(10))  # CT, CR/DX (CXR)
    study_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    series_count: Mapped[int] = mapped_column(Integer, default=0)
    instance_count: Mapped[int] = mapped_column(Integer, default=0)
    slice_thickness: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Pipeline status
    status: Mapped[str] = mapped_column(String(20), default="uploaded")
    # uploaded -> queued -> processing -> completed -> error
    pipeline_type: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ct, cxr
    overall_lung_rads: Mapped[str | None] = mapped_column(String(5), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="studies")
    nodules: Mapped[list["Nodule"]] = relationship(back_populates="study")
    report: Mapped["Report | None"] = relationship(back_populates="study", uselist=False)
