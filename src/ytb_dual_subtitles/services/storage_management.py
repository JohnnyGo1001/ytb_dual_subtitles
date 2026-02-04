"""Storage management service for YouTube dual-subtitles system.

This module provides storage statistics, cleanup suggestions and quota management.
"""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ytb_dual_subtitles.core.settings import get_settings


@dataclass
class StorageStats:
    """Storage usage statistics."""

    total_space: int = 0
    used_space: int = 0
    free_space: int = 0
    usage_percentage: float = 0.0
    video_count: int = 0
    total_video_size: int = 0


@dataclass
class CleanupSuggestion:
    """Cleanup suggestion information."""

    type: str
    description: str
    file_count: int
    space_saved: int
    risk_level: str  # "low", "medium", "high"


class StorageManagementService:
    """Service for storage management and optimization."""

    # Storage quota thresholds
    WARNING_THRESHOLD = 0.8   # 80% usage
    CRITICAL_THRESHOLD = 0.95  # 95% usage
    AUTO_CLEANUP_THRESHOLD = 0.9  # 90% usage

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize StorageManagementService.

        Args:
            db_session: Database session for data operations
        """
        self.db_session = db_session
        self.settings = get_settings()
        self.download_path = self.settings.download_path

    async def get_storage_statistics(self) -> StorageStats:
        """Get comprehensive storage usage statistics.

        Returns:
            Storage statistics including disk usage and video counts
        """
        try:
            # Get disk usage
            total, used, free = shutil.disk_usage(self.download_path)
            usage_percentage = (used / total) * 100 if total > 0 else 0.0

            # Calculate video file statistics
            video_count, total_video_size = await self._calculate_video_stats()

            return StorageStats(
                total_space=total,
                used_space=used,
                free_space=free,
                usage_percentage=usage_percentage,
                video_count=video_count,
                total_video_size=total_video_size
            )

        except OSError:
            # Return empty stats if disk access fails
            return StorageStats()

    async def analyze_cleanup_suggestions(self) -> list[CleanupSuggestion]:
        """Analyze storage and generate cleanup suggestions.

        Returns:
            List of cleanup suggestions with potential space savings
        """
        suggestions: list[CleanupSuggestion] = []

        # Check for temporary files
        temp_suggestion = await self._analyze_temp_files()
        if temp_suggestion.space_saved > 0:
            suggestions.append(temp_suggestion)

        # Check for duplicate files
        duplicate_suggestion = await self._analyze_duplicate_files()
        if duplicate_suggestion.space_saved > 0:
            suggestions.append(duplicate_suggestion)

        # Check for orphaned thumbnails
        orphan_suggestion = await self._analyze_orphaned_thumbnails()
        if orphan_suggestion.space_saved > 0:
            suggestions.append(orphan_suggestion)

        # Check for corrupted/inaccessible files
        broken_suggestion = await self._analyze_broken_files()
        if broken_suggestion.space_saved > 0:
            suggestions.append(broken_suggestion)

        return suggestions

    async def detect_duplicate_files(self) -> dict[str, list[Path]]:
        """Detect duplicate video files by content hash.

        Returns:
            Dictionary mapping file hashes to lists of duplicate file paths
        """
        file_hashes: dict[str, list[Path]] = {}

        # Supported video extensions
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'}

        for file_path in self.download_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                try:
                    file_hash = await self._calculate_file_hash(file_path)
                    if file_hash not in file_hashes:
                        file_hashes[file_hash] = []
                    file_hashes[file_hash].append(file_path)
                except (OSError, PermissionError):
                    # Skip files that can't be read
                    continue

        # Return only groups with duplicates
        return {hash_key: paths for hash_key, paths in file_hashes.items() if len(paths) > 1}

    async def clean_temp_files(self) -> tuple[int, int]:
        """Clean temporary and system files.

        Returns:
            Tuple of (files_deleted, space_freed)
        """
        temp_patterns = [
            '*.tmp', '*.temp', '*.part', '*.bak'
        ]

        # Specific files to delete
        specific_files = ['.DS_Store', 'Thumbs.db']

        deleted_count = 0
        space_freed = 0

        # Clean files matching patterns
        for pattern in temp_patterns:
            for file_path in self.download_path.glob(pattern):
                try:
                    if file_path.is_file():
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_count += 1
                        space_freed += file_size
                except (OSError, PermissionError):
                    # Continue with other files if one fails
                    continue

        # Clean specific files
        for filename in specific_files:
            file_path = self.download_path / filename
            if file_path.exists() and file_path.is_file():
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    space_freed += file_size
                except (OSError, PermissionError):
                    continue

        return deleted_count, space_freed

    async def clean_orphaned_thumbnails(self) -> tuple[int, int]:
        """Clean thumbnail files that have no corresponding video.

        Returns:
            Tuple of (files_deleted, space_freed)
        """
        from sqlalchemy import select
        from ytb_dual_subtitles.models.video import Video

        # Get all video file names from database
        stmt = select(Video.file_path).where(Video.file_path.is_not(None))
        result = await self.db_session.execute(stmt)
        video_paths = result.scalars().all()

        video_names = set()
        for video_path in video_paths:
            if video_path:
                video_names.add(Path(video_path).stem)

        # Check thumbnail directory
        # Try both possible locations: parent/thumbnails and download_path/thumbnails
        thumbnail_dir = self.download_path.parent / "thumbnails"
        if not thumbnail_dir.exists():
            thumbnail_dir = self.download_path / "thumbnails"
            if not thumbnail_dir.exists():
                return 0, 0

        deleted_count = 0
        space_freed = 0

        for thumb_path in thumbnail_dir.iterdir():
            if thumb_path.is_file():
                # Extract video name from thumbnail filename
                # Format: {video_name}_{size}.{ext}
                thumb_name_parts = thumb_path.stem.rsplit('_', 1)
                if len(thumb_name_parts) == 2:
                    video_name = thumb_name_parts[0]
                    if video_name not in video_names:
                        try:
                            file_size = thumb_path.stat().st_size
                            thumb_path.unlink()
                            deleted_count += 1
                            space_freed += file_size
                        except (OSError, PermissionError):
                            continue

        return deleted_count, space_freed

    async def check_storage_quota(self) -> dict[str, Any]:
        """Check storage quota and return status.

        Returns:
            Dictionary with quota status information
        """
        stats = await self.get_storage_statistics()

        usage_ratio = stats.usage_percentage / 100.0

        if usage_ratio >= self.CRITICAL_THRESHOLD:
            status = "critical"
            message = f"Critical: Storage is {stats.usage_percentage:.1f}% full. Immediate cleanup required."
        elif usage_ratio >= self.WARNING_THRESHOLD:
            status = "warning"
            message = f"Warning: Storage is {stats.usage_percentage:.1f}% full. Consider cleanup."
        else:
            status = "ok"
            message = f"Storage usage is normal ({stats.usage_percentage:.1f}%)."

        return {
            "status": status,
            "usage_percentage": stats.usage_percentage,
            "free_space": stats.free_space,
            "total_space": stats.total_space,
            "message": message,
            "auto_cleanup_needed": usage_ratio >= self.AUTO_CLEANUP_THRESHOLD
        }

    async def _calculate_video_stats(self) -> tuple[int, int]:
        """Calculate video file count and total size.

        Returns:
            Tuple of (video_count, total_size)
        """
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'}

        video_count = 0
        total_size = 0

        for file_path in self.download_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                try:
                    total_size += file_path.stat().st_size
                    video_count += 1
                except (OSError, PermissionError):
                    continue

        return video_count, total_size

    async def _calculate_file_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate MD5 hash of file content.

        Args:
            file_path: Path to file
            chunk_size: Size of chunks to read

        Returns:
            MD5 hash as hex string
        """
        hash_md5 = hashlib.md5()

        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    async def _analyze_temp_files(self) -> CleanupSuggestion:
        """Analyze temporary files for cleanup."""
        temp_patterns = [
            '*.tmp', '*.temp', '*.part', '*.bak'
        ]

        # Specific files to check
        specific_files = ['.DS_Store', 'Thumbs.db']

        file_count = 0
        total_size = 0

        # Check files matching patterns
        for pattern in temp_patterns:
            for file_path in self.download_path.glob(pattern):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                        file_count += 1
                    except (OSError, PermissionError):
                        continue

        # Check specific files
        for filename in specific_files:
            file_path = self.download_path / filename
            if file_path.exists() and file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                    file_count += 1
                except (OSError, PermissionError):
                    continue

        return CleanupSuggestion(
            type="temp_files",
            description=f"Temporary and system files ({file_count} files)",
            file_count=file_count,
            space_saved=total_size,
            risk_level="low"
        )

    async def _analyze_duplicate_files(self) -> CleanupSuggestion:
        """Analyze duplicate files for cleanup."""
        duplicates = await self.detect_duplicate_files()

        file_count = 0
        total_size = 0

        for file_group in duplicates.values():
            # Keep the first file, count others as deletable
            for file_path in file_group[1:]:
                try:
                    total_size += file_path.stat().st_size
                    file_count += 1
                except (OSError, PermissionError):
                    continue

        return CleanupSuggestion(
            type="duplicate_files",
            description=f"Duplicate video files ({file_count} duplicates)",
            file_count=file_count,
            space_saved=total_size,
            risk_level="medium"
        )

    async def _analyze_orphaned_thumbnails(self) -> CleanupSuggestion:
        """Analyze orphaned thumbnails for cleanup."""
        from sqlalchemy import select
        from ytb_dual_subtitles.models.video import Video

        # Get video names from database
        stmt = select(Video.file_path).where(Video.file_path.is_not(None))
        result = await self.db_session.execute(stmt)
        video_paths = result.scalars().all()

        video_names = set()
        for video_path in video_paths:
            if video_path:
                video_names.add(Path(video_path).stem)

        # Check thumbnails
        # Try both possible locations: parent/thumbnails and download_path/thumbnails
        thumbnail_dir = self.download_path.parent / "thumbnails"
        if not thumbnail_dir.exists():
            thumbnail_dir = self.download_path / "thumbnails"
            if not thumbnail_dir.exists():
                return CleanupSuggestion("orphaned_thumbnails", "No orphaned thumbnails", 0, 0, "low")

        file_count = 0
        total_size = 0

        for thumb_path in thumbnail_dir.iterdir():
            if thumb_path.is_file():
                thumb_name_parts = thumb_path.stem.rsplit('_', 1)
                if len(thumb_name_parts) == 2:
                    video_name = thumb_name_parts[0]
                    if video_name not in video_names:
                        try:
                            total_size += thumb_path.stat().st_size
                            file_count += 1
                        except (OSError, PermissionError):
                            continue

        return CleanupSuggestion(
            type="orphaned_thumbnails",
            description=f"Orphaned thumbnail files ({file_count} files)",
            file_count=file_count,
            space_saved=total_size,
            risk_level="low"
        )

    async def _analyze_broken_files(self) -> CleanupSuggestion:
        """Analyze broken/inaccessible files for cleanup."""
        from sqlalchemy import select
        from ytb_dual_subtitles.models.video import Video, VideoStatus

        # Find videos marked as ERROR status
        stmt = select(Video).where(Video.status == VideoStatus.ERROR)
        result = await self.db_session.execute(stmt)
        broken_videos = result.scalars().all()

        file_count = 0
        total_size = 0

        for video in broken_videos:
            if video.file_path:
                file_path = Path(video.file_path)
                if file_path.exists():
                    try:
                        total_size += file_path.stat().st_size
                        file_count += 1
                    except (OSError, PermissionError):
                        continue

        return CleanupSuggestion(
            type="broken_files",
            description=f"Corrupted or broken video files ({file_count} files)",
            file_count=file_count,
            space_saved=total_size,
            risk_level="high"
        )