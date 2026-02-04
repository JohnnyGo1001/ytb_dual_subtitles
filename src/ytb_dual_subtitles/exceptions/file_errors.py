"""File operation exceptions for the YouTube dual-subtitles system.

This module defines exceptions for file management operations.
"""

from __future__ import annotations

from enum import Enum


class FileErrorCode(Enum):
    """File operation error codes."""

    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    DISK_SPACE_FULL = "DISK_SPACE_FULL"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    CORRUPTION_DETECTED = "CORRUPTION_DETECTED"


class FileOperationError(Exception):
    """Base exception for file operations."""

    def __init__(self, message: str, error_code: FileErrorCode) -> None:
        """Initialize file operation error.

        Args:
            message: Error description
            error_code: Specific error code
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error message with code."""
        return f"[{self.error_code.value}] {self.message}"


class FileNotFoundError(FileOperationError):
    """Exception raised when file or directory is not found."""

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Directory not found: {path}",
            FileErrorCode.FILE_NOT_FOUND
        )


class PermissionDeniedError(FileOperationError):
    """Exception raised when file operation lacks permission."""

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Permission denied: {path}",
            FileErrorCode.PERMISSION_DENIED
        )


class DiskSpaceError(FileOperationError):
    """Exception raised when insufficient disk space."""

    def __init__(self, required: int, available: int) -> None:
        super().__init__(
            f"Insufficient disk space. Required: {required} bytes, Available: {available} bytes",
            FileErrorCode.DISK_SPACE_FULL
        )