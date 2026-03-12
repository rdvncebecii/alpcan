import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Nodule(Base):
    __tablename__ = "nodules"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    study_id: Mapped[str] = mapped_column(ForeignKey("studies.id"))

    # Location
    location_description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    coord_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    coord_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    coord_z: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Size
    diameter_mm: Mapped[float] = mapped_column(Float)
    volume_mm3: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Characterization
    density: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # solid, part-solid, ground-glass
    morphology: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # smooth, lobulated, spiculated, irregular

    # Scores
    malignancy_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0-1.0
    detection_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    lung_rads_category: Mapped[str | None] = mapped_column(String(5), nullable=True)

    # Growth tracking (compared to previous study)
    previous_diameter_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_doubling_time_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    growth_rate_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Grad-CAM heatmap path
    heatmap_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Agent metadata
    agent_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    study: Mapped["Study"] = relationship(back_populates="nodules")
