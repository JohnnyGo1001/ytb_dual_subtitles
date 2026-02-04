"""Player API routes for YouTube dual-subtitles system.

This module provides REST API endpoints for video player functionality:
- Video data retrieval with subtitles
- Player configuration management
- Playback progress tracking
- Analytics and statistics
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field, validator

from ytb_dual_subtitles.models import (
    ApiResponse,
    ErrorCodes,
)

# Initialize router
router = APIRouter(tags=["player"])


# Request/Response models
class PlayerConfig(BaseModel):
    """Player configuration model."""

    sync_tolerance: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Subtitle sync tolerance in seconds (±100ms default)"
    )
    default_volume: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Default volume level (0.0-1.0)"
    )
    playback_rates: List[float] = Field(
        default=[0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
        description="Available playback speed options"
    )
    auto_play: bool = Field(
        default=False,
        description="Enable auto-play when video loads"
    )
    subtitle_delay: float = Field(
        default=0.0,
        ge=-5.0,
        le=5.0,
        description="Global subtitle delay in seconds"
    )

    @validator("playback_rates")
    def validate_playback_rates(cls, v):
        """Validate playback rates are within acceptable range."""
        for rate in v:
            if not (0.25 <= rate <= 4.0):
                raise ValueError("Playback rates must be between 0.25 and 4.0")
        return sorted(set(v))  # Remove duplicates and sort


class ProgressRequest(BaseModel):
    """Request model for saving playback progress."""

    video_id: str = Field(..., description="Video identifier")
    current_time: float = Field(
        ..., ge=0.0, description="Current playback position in seconds"
    )
    duration: float = Field(
        ..., ge=0.0, description="Total video duration in seconds"
    )

    @validator("current_time")
    def validate_current_time(cls, v, values):
        """Validate current time doesn't exceed duration."""
        duration = values.get("duration", 0)
        if duration > 0 and v > duration:
            raise ValueError("Current time cannot exceed video duration")
        return v


class PlaybackEvent(BaseModel):
    """Model for playback analytics events."""

    video_id: str = Field(..., description="Video identifier")
    event_type: str = Field(..., description="Type of playback event")
    current_time: float = Field(
        ..., ge=0.0, description="Time when event occurred"
    )
    session_id: str = Field(..., description="User session identifier")
    timestamp: Optional[datetime] = Field(
        default=None, description="Event timestamp (auto-generated if not provided)"
    )

    @validator("event_type")
    def validate_event_type(cls, v):
        """Validate event type is one of allowed values."""
        allowed_events = {
            "play", "pause", "seek", "volume_change", "speed_change",
            "fullscreen", "subtitle_toggle", "complete", "error"
        }
        if v not in allowed_events:
            raise ValueError(f"Invalid event type. Must be one of: {allowed_events}")
        return v


class VideoPlayerResponse(BaseModel):
    """Response model for video player data."""

    video: Dict[str, Any]
    subtitles: List[Dict[str, Any]]
    player_config: Optional[PlayerConfig] = None


class SubtitleResponse(BaseModel):
    """Response model for subtitle data at specific time."""

    subtitles: List[Dict[str, Any]]
    time: float
    total_count: int


class ProgressResponse(BaseModel):
    """Response model for playback progress."""

    video_id: str
    current_time: float
    duration: float
    last_updated: datetime
    completion_percentage: float


class StatisticsResponse(BaseModel):
    """Response model for video statistics."""

    video_id: str
    total_views: int
    total_watch_time: float
    average_session_duration: float
    completion_rate: float
    last_viewed: Optional[datetime]


# Global player configuration (in production, this would be stored in database)
_player_config = PlayerConfig()


# Mock services (will be replaced with real services)
class MockVideoService:
    """Mock video service for testing."""

    @staticmethod
    def get_video_with_subtitles(video_id: str) -> Optional[Dict[str, Any]]:
        """Get video data with subtitles."""
        if video_id == "test_video_1":
            return {
                "video": {
                    "id": video_id,
                    "title": "Test Video",
                    "file_path": "/path/to/video.mp4",
                    "duration": 300.5,
                    "thumbnail_url": "https://example.com/thumb.jpg"
                },
                "subtitles": [
                    {
                        "id": 1,
                        "start_time": 0.0,
                        "end_time": 2.5,
                        "text": "Hello world",
                        "language": "en"
                    }
                ]
            }
        return None


class MockSubtitleService:
    """Mock subtitle service for testing."""

    @staticmethod
    def get_subtitles_at_time(video_id: str, time: float) -> List[Dict[str, Any]]:
        """Get subtitles at specific time."""
        return [
            {
                "id": 1,
                "start_time": 0.0,
                "end_time": 2.5,
                "text": "Hello world",
                "language": "en"
            }
        ]


class MockPlaybackService:
    """Mock playback service for testing."""

    _progress_store = {}

    @classmethod
    def save_progress(cls, video_id: str, current_time: float, duration: float) -> bool:
        """Save playback progress."""
        cls._progress_store[video_id] = {
            "video_id": video_id,
            "current_time": current_time,
            "duration": duration,
            "last_updated": datetime.now()
        }
        return True

    @classmethod
    def get_progress(cls, video_id: str) -> Optional[Dict[str, Any]]:
        """Get saved playback progress."""
        return cls._progress_store.get(video_id)


class MockAnalyticsService:
    """Mock analytics service for testing."""

    @staticmethod
    def get_video_stats(video_id: str) -> Dict[str, Any]:
        """Get video statistics."""
        return {
            "video_id": video_id,
            "total_views": 5,
            "total_watch_time": 1500.0,
            "average_session_duration": 300.0,
            "completion_rate": 0.85
        }

    @staticmethod
    def record_event(
        video_id: str, event_type: str, current_time: float, session_id: str
    ) -> bool:
        """Record playback event."""
        return True


# API Routes

@router.get("/video/{video_id}", response_model=VideoPlayerResponse)
async def get_video_player_data(video_id: str) -> VideoPlayerResponse:
    """Get video data with subtitles for player initialization.

    Args:
        video_id: Unique video identifier

    Returns:
        Video data including metadata and subtitle segments

    Raises:
        HTTPException: 404 if video not found, 500 for server errors
    """
    try:
        data = MockVideoService.get_video_with_subtitles(video_id)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video with ID '{video_id}' not found"
            )

        return VideoPlayerResponse(
            video=data["video"],
            subtitles=data["subtitles"],
            player_config=_player_config
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )


@router.get("/video/{video_id}/subtitles", response_model=SubtitleResponse)
async def get_video_subtitles_at_time(
    video_id: str,
    time: float = Query(..., ge=0.0, description="Time in seconds")
) -> SubtitleResponse:
    """Get subtitles active at specific playback time.

    Args:
        video_id: Unique video identifier
        time: Playback time in seconds

    Returns:
        Subtitle segments active at the specified time
    """
    subtitles = MockSubtitleService.get_subtitles_at_time(video_id, time)

    return SubtitleResponse(
        subtitles=subtitles,
        time=time,
        total_count=len(subtitles)
    )


@router.get("/config", response_model=PlayerConfig)
async def get_player_config() -> PlayerConfig:
    """Get current player configuration.

    Returns:
        Current player configuration settings
    """
    return _player_config


@router.put("/config", response_model=PlayerConfig)
async def update_player_config(config: PlayerConfig) -> PlayerConfig:
    """Update player configuration.

    Args:
        config: New player configuration

    Returns:
        Updated player configuration
    """
    global _player_config
    _player_config = config
    return _player_config


@router.post("/progress")
async def save_playback_progress(request: ProgressRequest) -> Dict[str, Any]:
    """Save video playback progress.

    Args:
        request: Progress data to save

    Returns:
        Success confirmation
    """
    success = MockPlaybackService.save_progress(
        request.video_id, request.current_time, request.duration
    )

    return {"success": success}


@router.get("/progress/{video_id}", response_model=ProgressResponse)
async def get_playback_progress(video_id: str) -> ProgressResponse:
    """Get saved playback progress for a video.

    Args:
        video_id: Unique video identifier

    Returns:
        Saved playback progress data

    Raises:
        HTTPException: 404 if no progress found
    """
    progress = MockPlaybackService.get_progress(video_id)
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No playback progress found for video '{video_id}'"
        )

    completion_percentage = (
        (progress["current_time"] / progress["duration"]) * 100
        if progress["duration"] > 0 else 0.0
    )

    return ProgressResponse(
        video_id=progress["video_id"],
        current_time=progress["current_time"],
        duration=progress["duration"],
        last_updated=progress["last_updated"],
        completion_percentage=completion_percentage
    )


@router.get("/video/{video_id}/stats", response_model=StatisticsResponse)
async def get_video_statistics(video_id: str) -> StatisticsResponse:
    """Get playback statistics for a video.

    Args:
        video_id: Unique video identifier

    Returns:
        Video playback statistics and analytics
    """
    stats = MockAnalyticsService.get_video_stats(video_id)

    return StatisticsResponse(
        video_id=stats["video_id"],
        total_views=stats["total_views"],
        total_watch_time=stats["total_watch_time"],
        average_session_duration=stats["average_session_duration"],
        completion_rate=stats["completion_rate"],
        last_viewed=None  # Would be populated from database
    )


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def record_playback_event(event: PlaybackEvent) -> Dict[str, Any]:
    """Record a playback event for analytics.

    Args:
        event: Playback event data

    Returns:
        Recording confirmation
    """
    # Set timestamp if not provided
    if not event.timestamp:
        event.timestamp = datetime.now()

    recorded = MockAnalyticsService.record_event(
        event.video_id, event.event_type, event.current_time, event.session_id
    )

    return {"recorded": recorded, "timestamp": event.timestamp}