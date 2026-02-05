"""Database models for YouTube dual-subtitles system.

This module defines SQLAlchemy 2.0 models for videos, subtitles, download tasks,
and subtitle segments.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class VideoStatus(str, Enum):
    """Video processing status enumeration."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    ERROR = "error"


class DownloadTaskStatus(str, Enum):
    """Download task status enumeration."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class SubtitleSourceType(str, Enum):
    """Subtitle source type enumeration."""

    YOUTUBE = "youtube"
    TRANSLATED = "translated"
    MANUAL = "manual"


class Video(Base):
    """Video model for storing downloaded YouTube videos."""

    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    youtube_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, index=True)  # Add index for title-based deduplication
    description: Mapped[str | None] = mapped_column(Text)
    duration: Mapped[int | None] = mapped_column(Integer)  # Duration in seconds
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100), default="未分类", index=True)  # Video category
    channel_name: Mapped[str | None] = mapped_column(String(200), index=True)  # Channel name for auto-categorization
    status: Mapped[VideoStatus] = mapped_column(
        String(20),
        default=VideoStatus.PENDING,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    subtitles: Mapped[list[Subtitle]] = relationship(
        "Subtitle",
        back_populates="video",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, youtube_id='{self.youtube_id}', title='{self.title[:50]}...')>"


class Subtitle(Base):
    """Subtitle model for storing video subtitles."""

    __tablename__ = "subtitles"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"),
        index=True
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    language_name: Mapped[str | None] = mapped_column(String(50))  # Display name for language
    source_type: Mapped[SubtitleSourceType] = mapped_column(
        String(20),
        default=SubtitleSourceType.YOUTUBE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    video: Mapped[Video] = relationship("Video", back_populates="subtitles")
    segments: Mapped[list[SubtitleSegment]] = relationship(
        "SubtitleSegment",
        back_populates="subtitle",
        cascade="all, delete-orphan",
        order_by="SubtitleSegment.sequence"
    )

    __table_args__ = (
        UniqueConstraint('video_id', 'language', 'source_type', name='_video_lang_source_uc'),
    )

    def __repr__(self) -> str:
        return f"<Subtitle(id={self.id}, video_id={self.video_id}, language='{self.language}', source='{self.source_type}')>"


class SubtitleSegment(Base):
    """Individual subtitle segment with timing and text."""

    __tablename__ = "subtitle_segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    subtitle_id: Mapped[int] = mapped_column(
        ForeignKey("subtitles.id", ondelete="CASCADE"),
        index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[float] = mapped_column(nullable=False)  # Start time in seconds
    end_time: Mapped[float] = mapped_column(nullable=False)    # End time in seconds
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    subtitle: Mapped[Subtitle] = relationship("Subtitle", back_populates="segments")

    __table_args__ = (
        UniqueConstraint('subtitle_id', 'sequence', name='_subtitle_sequence_uc'),
    )

    def __repr__(self) -> str:
        return f"<SubtitleSegment(id={self.id}, sequence={self.sequence}, start={self.start_time}, end={self.end_time})>"

    @property
    def duration(self) -> float:
        """Calculate segment duration in seconds."""
        return self.end_time - self.start_time


class DownloadTask(Base):
    """Download task model for tracking video download progress."""

    __tablename__ = "download_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    youtube_url: Mapped[str] = mapped_column(Text, nullable=False)
    video_id: Mapped[int | None] = mapped_column(
        ForeignKey("videos.id", ondelete="SET NULL"),
        index=True
    )
    status: Mapped[DownloadTaskStatus] = mapped_column(
        String(20),
        default=DownloadTaskStatus.PENDING,
        index=True
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)  # Progress percentage 0-100
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    video: Mapped[Video | None] = relationship("Video")

    def __repr__(self) -> str:
        return f"<DownloadTask(id={self.id}, status='{self.status}', progress={self.progress}%)>"

    @property
    def is_active(self) -> bool:
        """Check if the download task is currently active."""
        return self.status in {DownloadTaskStatus.PENDING, DownloadTaskStatus.DOWNLOADING}

    @property
    def is_completed(self) -> bool:
        """Check if the download task has completed successfully."""
        return self.status == DownloadTaskStatus.COMPLETED

    @property
    def has_error(self) -> bool:
        """Check if the download task has encountered an error."""
        return self.status == DownloadTaskStatus.ERROR