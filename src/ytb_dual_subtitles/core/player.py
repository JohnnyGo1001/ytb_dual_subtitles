"""Player core logic for YouTube dual-subtitles system.

This module provides the core player functionality including:
- Video playback state management with immutable snapshots
- Subtitle synchronization with ±100ms precision tolerance
- Playback controls (play/pause, seek, volume, speed, fullscreen)
- Dual-language subtitle display support

The PlayerCore class follows the CQRS pattern with separate command and query
methods to maintain clear separation of concerns.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# Player constants
DEFAULT_SYNC_TOLERANCE = 0.1  # ±100ms subtitle sync tolerance
MIN_VOLUME = 0.0
MAX_VOLUME = 1.0
MIN_PLAYBACK_RATE = 0.25
MAX_PLAYBACK_RATE = 2.0
DEFAULT_VOLUME = 1.0
DEFAULT_PLAYBACK_RATE = 1.0


class PlayerError(Exception):
    """Exception raised for player-related errors."""
    pass


class SubtitleSegment:
    """Represents a subtitle segment with timing and text."""

    def __init__(
        self,
        id: int,
        start_time: float,
        end_time: float,
        text: str,
        language: str
    ) -> None:
        self.id = id
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        self.language = language

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SubtitleSegment:
        """Create SubtitleSegment from dictionary data."""
        try:
            return cls(
                id=data["id"],
                start_time=float(data["start_time"]),
                end_time=float(data["end_time"]),
                text=data["text"],
                language=data["language"]
            )
        except (KeyError, TypeError, ValueError) as e:
            raise PlayerError(f"Invalid subtitle format: {e}") from e

    @property
    def duration(self) -> float:
        """Calculate segment duration in seconds."""
        return self.end_time - self.start_time

    def contains_time(self, time: float, tolerance: float = 0.1) -> bool:
        """Check if the given time is within this segment's time range with tolerance.

        Args:
            time: Time to check in seconds
            tolerance: Time tolerance in seconds (±100ms by default)

        Returns:
            True if time is within segment bounds including tolerance
        """
        return (self.start_time - tolerance) <= time <= (self.end_time + tolerance)


class PlayerState:
    """Immutable player state snapshot."""

    def __init__(
        self,
        current_time: float = 0.0,
        duration: float = 0.0,
        is_playing: bool = False,
        volume: float = DEFAULT_VOLUME,
        is_muted: bool = False,
        playback_rate: float = DEFAULT_PLAYBACK_RATE,
        is_fullscreen: bool = False,
        current_subtitle: Optional[List[SubtitleSegment]] = None
    ) -> None:
        self.current_time = current_time
        self.duration = duration
        self.is_playing = is_playing
        self.volume = volume
        self.is_muted = is_muted
        self.playback_rate = playback_rate
        self.is_fullscreen = is_fullscreen
        self.current_subtitle = current_subtitle

    def copy(self, **changes: Any) -> "PlayerState":
        """Create a copy of the state with specified changes."""
        # Get current values
        current_values = {
            "current_time": self.current_time,
            "duration": self.duration,
            "is_playing": self.is_playing,
            "volume": self.volume,
            "is_muted": self.is_muted,
            "playback_rate": self.playback_rate,
            "is_fullscreen": self.is_fullscreen,
            "current_subtitle": self.current_subtitle,
        }
        # Apply changes
        current_values.update(changes)
        return PlayerState(**current_values)

    def __eq__(self, other: Any) -> bool:
        """Check equality with another PlayerState."""
        if not isinstance(other, PlayerState):
            return False
        return (
            self.current_time == other.current_time
            and self.duration == other.duration
            and self.is_playing == other.is_playing
            and self.volume == other.volume
            and self.is_muted == other.is_muted
            and self.playback_rate == other.playback_rate
            and self.is_fullscreen == other.is_fullscreen
            and self.current_subtitle == other.current_subtitle
        )


class PlayerCore:
    """Core player functionality for video playback and subtitle synchronization.

    Provides video playback control, subtitle synchronization with ±100ms precision,
    and state management for the video player.
    """

    def __init__(
        self,
        video_data: Dict[str, Any],
        subtitle_segments: List[Dict[str, Any]],
        sync_tolerance: float = DEFAULT_SYNC_TOLERANCE
    ) -> None:
        """Initialize PlayerCore with video data and subtitles.

        Args:
            video_data: Video metadata including id, title, file_path, duration
            subtitle_segments: List of subtitle segment dictionaries
            sync_tolerance: Subtitle sync tolerance in seconds (±100ms by default)

        Raises:
            PlayerError: If video data is invalid or subtitle format is incorrect
        """
        self.sync_tolerance = sync_tolerance
        self._validate_video_data(video_data)
        self.video_data = video_data

        # Parse and validate subtitle segments
        self.subtitle_segments = []
        for segment_data in subtitle_segments:
            segment = SubtitleSegment.from_dict(segment_data)
            self.subtitle_segments.append(segment)

        # Initialize player state
        self._state = PlayerState(
            duration=float(video_data["duration"]),
            current_time=0.0
        )
        self._previous_volume = DEFAULT_VOLUME  # For mute/unmute functionality

    def _validate_video_data(self, data: Dict[str, Any]) -> None:
        """Validate video data contains required fields."""
        required_fields = ["id", "title", "file_path", "duration"]
        if not data or not all(field in data for field in required_fields):
            raise PlayerError("Invalid video data: missing required fields")

    @property
    def state(self) -> PlayerState:
        """Get current player state (immutable snapshot)."""
        # Return a copy to maintain immutability
        return self._state.copy()

    def play(self) -> None:
        """Start video playback."""
        self._state = self._state.copy(is_playing=True)

    def pause(self) -> None:
        """Pause video playback."""
        self._state = self._state.copy(is_playing=False)

    def toggle_play(self) -> None:
        """Toggle play/pause state."""
        if self._state.is_playing:
            self.pause()
        else:
            self.play()

    def seek(self, time: float) -> None:
        """Seek to specific time position.

        Args:
            time: Target time in seconds (will be clamped to valid range)
        """
        # Clamp time to valid range [0, duration]
        clamped_time = max(0.0, min(time, self._state.duration))
        self._state = self._state.copy(current_time=clamped_time)

    def set_volume(self, volume: float) -> None:
        """Set playback volume.

        Args:
            volume: Volume level (will be clamped to [0.0, 1.0])
        """
        # Clamp volume to valid range
        clamped_volume = max(MIN_VOLUME, min(volume, MAX_VOLUME))

        # If we're unmuting and setting volume > 0, update unmuted state
        is_muted = self._state.is_muted and clamped_volume == 0.0

        self._state = self._state.copy(
            volume=clamped_volume,
            is_muted=is_muted
        )

        # Remember volume for unmute
        if clamped_volume > 0.0:
            self._previous_volume = clamped_volume

    def mute(self) -> None:
        """Mute audio."""
        if not self._state.is_muted:
            self._previous_volume = self._state.volume
        self._state = self._state.copy(volume=0.0, is_muted=True)

    def unmute(self) -> None:
        """Unmute audio, restoring previous volume."""
        self._state = self._state.copy(
            volume=self._previous_volume,
            is_muted=False
        )

    def toggle_mute(self) -> None:
        """Toggle mute state."""
        if self._state.is_muted:
            self.unmute()
        else:
            self.mute()

    def set_playback_rate(self, rate: float) -> None:
        """Set playback rate.

        Args:
            rate: Playback rate (will be clamped to [0.25, 2.0])
        """
        # Clamp playback rate to valid range
        clamped_rate = max(MIN_PLAYBACK_RATE, min(rate, MAX_PLAYBACK_RATE))
        self._state = self._state.copy(playback_rate=clamped_rate)

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        self._state = self._state.copy(is_fullscreen=not self._state.is_fullscreen)

    def get_current_subtitles(self, time: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get subtitle segments for the specified time with efficient lookup.

        Uses linear search for current implementation, which can be optimized
        to binary search if performance becomes an issue with large subtitle sets.

        Args:
            time: Time to get subtitles for. If None, uses current playback time.

        Returns:
            List of subtitle segments active at the specified time, grouped by language
        """
        target_time = time if time is not None else self._state.current_time

        # Optimized: collect matching segments in single pass
        current_subtitles = [
            {
                "id": segment.id,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "text": segment.text,
                "language": segment.language
            }
            for segment in self.subtitle_segments
            if segment.contains_time(target_time, self.sync_tolerance)
        ]

        return current_subtitles