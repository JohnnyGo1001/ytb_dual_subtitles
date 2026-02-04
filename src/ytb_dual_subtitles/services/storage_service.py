"""Storage service for file management.

Task 5: 存储服务集成
Subtasks 5.1-5.5: Complete implementation following TDD approach
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from ytb_dual_subtitles.core.settings import get_settings
from ytb_dual_subtitles.exceptions.download_errors import (
    InsufficientSpaceError,
    InvalidFilePathError,
    StorageError,
)


class StorageService:
    """Storage service for file management and validation.

    Provides secure file operations, path validation, and storage management
    for the YouTube dual-subtitles system.
    """

    def __init__(self) -> None:
        """Initialize StorageService with settings."""
        self.settings = get_settings()
        self.download_path = self.settings.download_path
        self.max_file_size = getattr(self.settings, 'max_file_size', 5 * 1024 * 1024 * 1024)

        # Ensure download directory exists
        self.download_path.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing/replacing unsafe characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem use
        """
        if not filename or filename.strip() in ("", ".", ".."):
            return "untitled"

        # Remove/replace unsafe characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)

        # Limit length to prevent filesystem issues
        if len(sanitized) > 200:
            sanitized = sanitized[:200]

        return sanitized.strip()

    def generate_file_path(self, youtube_id: str, title: str) -> Path:
        """Generate secure file path for a video.

        Args:
            youtube_id: YouTube video ID
            title: Video title

        Returns:
            Full file path for the video
        """
        sanitized_title = self.sanitize_filename(title)
        filename = f"{youtube_id}_{sanitized_title}.mp4"

        base_path = self.download_path / filename

        # Handle duplicates by appending counter
        if base_path.exists():
            counter = 1
            stem = base_path.stem
            suffix = base_path.suffix
            while base_path.exists():
                new_filename = f"{stem}_{counter}{suffix}"
                base_path = self.download_path / new_filename
                counter += 1

        return base_path

    def generate_file_path_from_url(self, filename_from_url: str) -> Path:
        """Generate file path based on URL-derived filename.

        Args:
            filename_from_url: Filename generated from URL (e.g., watch_v_abc123.mp4)

        Returns:
            Full file path for the video
        """
        # Sanitize the URL-based filename
        sanitized_filename = self.sanitize_filename(filename_from_url)
        base_path = self.download_path / sanitized_filename
        return base_path

    def check_file_exists(self, file_path: Path) -> bool:
        """Check if file already exists.

        Args:
            file_path: Path to check

        Returns:
            True if file exists, False otherwise
        """
        return file_path.exists() and file_path.is_file()

    def get_existing_file_info(self, file_path: Path) -> dict[str, Any] | None:
        """Get information about existing file.

        Args:
            file_path: Path to existing file

        Returns:
            Dictionary with file information or None if file doesn't exist
        """
        if not self.check_file_exists(file_path):
            return None

        try:
            stat_info = file_path.stat()
            return {
                "path": str(file_path),
                "size": stat_info.st_size,
                "modified": stat_info.st_mtime,
                "filename": file_path.name,
                "exists": True
            }
        except OSError:
            return None

    async def check_disk_space(self, required_size: int) -> None:
        """Check if sufficient disk space is available.

        Args:
            required_size: Required space in bytes

        Raises:
            InsufficientSpaceError: If insufficient space available
            StorageError: If disk usage check fails
        """
        try:
            total, used, free = shutil.disk_usage(self.download_path)
            if free < required_size:
                raise InsufficientSpaceError(
                    f"Insufficient disk space. Required: {required_size} bytes, "
                    f"Available: {free} bytes"
                )
        except OSError as e:
            raise StorageError(f"Failed to check disk space: {e}") from e

    async def ensure_directory_exists(self, directory: Path) -> None:
        """Ensure directory exists, create if necessary.

        Args:
            directory: Directory path to ensure exists

        Raises:
            StorageError: If directory creation fails or path is a file
        """
        try:
            if directory.exists() and not directory.is_dir():
                raise StorageError(f"Path exists but is not a directory: {directory}")

            directory.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise StorageError(f"Failed to create directory {directory}: {e}") from e

    async def validate_file_path(self, file_path: Path) -> None:
        """Validate file path for security (prevent path traversal attacks).

        Args:
            file_path: File path to validate

        Raises:
            InvalidFilePathError: If path is invalid or unsafe
        """
        try:
            # Resolve to absolute path and check if it's within download directory
            resolved_path = file_path.resolve()
            download_resolved = self.download_path.resolve()

            if not str(resolved_path).startswith(str(download_resolved)):
                raise InvalidFilePathError(
                    f"Path is outside download directory: {resolved_path}"
                )
        except (OSError, ValueError) as e:
            raise InvalidFilePathError(f"Invalid file path: {e}") from e

    async def cleanup_temp_files(self) -> None:
        """Clean up temporary files in download directory.

        Removes files with temporary extensions (.part, .tmp, .temp).
        Continues cleanup even if individual files fail to delete.
        """
        try:
            for file_path in self.download_path.iterdir():
                if self.is_temp_file(file_path.name):
                    try:
                        file_path.unlink()
                    except (OSError, PermissionError):
                        # Log error but continue cleanup
                        # In production, this should use proper logging
                        pass
        except OSError:
            # Directory might not exist or be accessible
            pass

    def is_temp_file(self, filename: str) -> bool:
        """Check if a file is temporary based on extension.

        Args:
            filename: Name of the file to check

        Returns:
            True if file is temporary, False otherwise
        """
        temp_extensions = ('.part', '.tmp', '.temp')
        return filename.lower().endswith(temp_extensions)

    def get_file_extension(self, filename: str) -> str:
        """Get file extension, default to .mp4 for videos.

        Args:
            filename: Original filename

        Returns:
            File extension including the dot
        """
        if not filename:
            return '.mp4'

        ext = Path(filename).suffix.lower()
        return ext if ext else '.mp4'

    async def calculate_file_size(self, file_path: Path) -> int:
        """Calculate file size in bytes.

        Args:
            file_path: Path to the file

        Returns:
            File size in bytes, 0 if file doesn't exist
        """
        try:
            return file_path.stat().st_size
        except (OSError, FileNotFoundError):
            return 0

    def get_disk_usage(self) -> dict[str, int]:
        """Get disk usage information for download directory.

        Returns:
            Dictionary with disk usage statistics
        """
        try:
            total, used, free = shutil.disk_usage(self.download_path)
            return {
                "total": total,
                "used": used,
                "free": free,
                "percentage": int((used / total) * 100) if total > 0 else 0
            }
        except Exception:
            return {"total": 0, "used": 0, "free": 0, "percentage": 0}