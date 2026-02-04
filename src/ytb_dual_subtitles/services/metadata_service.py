"""Video metadata extraction service for YouTube dual-subtitles system.

This module provides video metadata extraction and thumbnail generation functionality.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ffmpeg
from PIL import Image

from ytb_dual_subtitles.exceptions.file_errors import FileOperationError, FileErrorCode


@dataclass
class VideoMetadata:
    """Video metadata information."""

    duration: float = 0.0
    file_size: int = 0
    resolution: tuple[int, int] = (0, 0)
    codec: str = ""
    bitrate: int = 0
    fps: float = 0.0


@dataclass
class ThumbnailInfo:
    """Thumbnail information."""

    path: Path
    size: str
    format: str
    width: int
    height: int


class MetadataExtractionError(FileOperationError):
    """Exception raised when metadata extraction fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, FileErrorCode.CORRUPTION_DETECTED)


class MetadataService:
    """Service for extracting video metadata and generating thumbnails."""

    # Thumbnail size configurations
    THUMBNAIL_SIZES = {
        'small': (150, 84),
        'medium': (300, 168),
        'large': (480, 270)
    }

    # Supported video formats
    SUPPORTED_FORMATS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'}

    def __init__(self) -> None:
        """Initialize MetadataService."""
        self._metadata_cache: dict[str, VideoMetadata] = {}

    def _get_file_hash(self, file_path: Path) -> str:
        """Generate hash for file caching."""
        stat = file_path.stat()
        content = f"{file_path}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()

    async def extract_metadata(self, video_path: Path) -> VideoMetadata:
        """Extract video metadata using ffmpeg.

        Args:
            video_path: Path to video file

        Returns:
            Video metadata information

        Raises:
            MetadataExtractionError: If metadata extraction fails
        """
        if not video_path.exists():
            raise MetadataExtractionError(f"File not found: {video_path}")

        # Check cache first
        file_hash = self._get_file_hash(video_path)
        if file_hash in self._metadata_cache:
            return self._metadata_cache[file_hash]

        try:
            # Use ffprobe to extract metadata
            probe = ffmpeg.probe(str(video_path))

            # Extract format information
            format_info = probe.get('format', {})
            duration = float(format_info.get('duration', 0))
            file_size = int(format_info.get('size', 0))
            bitrate = int(format_info.get('bit_rate', 0))

            # Extract video stream information
            video_stream = None
            for stream in probe.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break

            if video_stream:
                width = int(video_stream.get('width', 0))
                height = int(video_stream.get('height', 0))
                codec = video_stream.get('codec_name', '')
                fps_str = video_stream.get('r_frame_rate', '0/1')
                try:
                    num, den = map(int, fps_str.split('/'))
                    fps = num / den if den != 0 else 0.0
                except (ValueError, ZeroDivisionError):
                    fps = 0.0
            else:
                width, height, codec, fps = 0, 0, '', 0.0

            metadata = VideoMetadata(
                duration=duration,
                file_size=file_size,
                resolution=(width, height),
                codec=codec,
                bitrate=bitrate,
                fps=fps
            )

            # Cache the result
            self._metadata_cache[file_hash] = metadata
            return metadata

        except Exception as e:
            raise MetadataExtractionError(f"Failed to extract metadata: {e}")

    async def generate_thumbnails(
        self,
        video_path: Path,
        output_dir: Path,
        timestamp: float = 10.0
    ) -> dict[str, ThumbnailInfo]:
        """Generate thumbnails of different sizes.

        Args:
            video_path: Path to video file
            output_dir: Directory to save thumbnails
            timestamp: Time position for thumbnail (seconds)

        Returns:
            Dictionary of thumbnail information by size

        Raises:
            MetadataExtractionError: If thumbnail generation fails
        """
        if not video_path.exists():
            raise MetadataExtractionError(f"Video file not found: {video_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        thumbnails: dict[str, ThumbnailInfo] = {}

        try:
            for size_name, (width, height) in self.THUMBNAIL_SIZES.items():
                # Generate thumbnail filename
                base_name = video_path.stem
                thumbnail_path = output_dir / f"{base_name}_{size_name}.webp"

                try:
                    # Use ffmpeg to extract thumbnail
                    (
                        ffmpeg
                        .input(str(video_path), ss=timestamp)
                        .output(
                            str(thumbnail_path),
                            vframes=1,
                            vf=f'scale={width}:{height}',
                            format='webp'
                        )
                        .overwrite_output()
                        .run(quiet=True)
                    )

                    thumbnails[size_name] = ThumbnailInfo(
                        path=thumbnail_path,
                        size=f"{width}x{height}",
                        format="webp",
                        width=width,
                        height=height
                    )

                except Exception as e:
                    # Try JPEG as fallback
                    jpeg_path = output_dir / f"{base_name}_{size_name}.jpeg"
                    try:
                        (
                            ffmpeg
                            .input(str(video_path), ss=timestamp)
                            .output(
                                str(jpeg_path),
                                vframes=1,
                                vf=f'scale={width}:{height}',
                                format='image2',
                                vcodec='mjpeg'
                            )
                            .overwrite_output()
                            .run(quiet=True)
                        )

                        thumbnails[size_name] = ThumbnailInfo(
                            path=jpeg_path,
                            size=f"{width}x{height}",
                            format="jpeg",
                            width=width,
                            height=height
                        )
                    except Exception:
                        raise MetadataExtractionError(f"Failed to generate thumbnail: {e}")

            return thumbnails

        except Exception as e:
            raise MetadataExtractionError(f"Failed to generate thumbnails: {e}")

    async def extract_batch_metadata(
        self,
        video_files: list[Path]
    ) -> dict[Path, VideoMetadata]:
        """Extract metadata from multiple video files.

        Args:
            video_files: List of video file paths

        Returns:
            Dictionary mapping file paths to metadata
        """
        results: dict[Path, VideoMetadata] = {}

        for video_path in video_files:
            try:
                metadata = await self.extract_metadata(video_path)
                results[video_path] = metadata
            except MetadataExtractionError:
                # Skip files that fail extraction
                continue

        return results

    def is_supported_format(self, file_path: Path) -> bool:
        """Check if file format is supported.

        Args:
            file_path: Path to check

        Returns:
            True if format is supported, False otherwise
        """
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS

    def clear_cache(self) -> None:
        """Clear metadata cache."""
        self._metadata_cache.clear()