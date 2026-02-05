"""Category model for video classification."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ytb_dual_subtitles.models.video import Base


class Category(Base):
    """Category model for organizing videos."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    color: Mapped[str | None] = mapped_column(String(20))  # Hex color code
    icon: Mapped[str | None] = mapped_column(String(50))  # Icon name or emoji
    sort_order: Mapped[int] = mapped_column(Integer, default=0)  # For custom ordering
    is_system: Mapped[bool] = mapped_column(default=False)  # System categories cannot be deleted
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"
