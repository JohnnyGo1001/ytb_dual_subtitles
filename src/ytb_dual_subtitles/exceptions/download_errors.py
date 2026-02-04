"""Download-related exceptions.

Subtask 6.1: 定义下载相关异常类
"""

from __future__ import annotations


class DownloadError(Exception):
    """Base exception for download-related errors."""

    def __init__(self, message: str) -> None:
        """Initialize download error.

        Args:
            message: Error message
        """
        self.message = message
        super().__init__(message)


class VideoNotFoundError(DownloadError):
    """Exception raised when a video is not found."""

    pass


class NetworkError(DownloadError):
    """Exception raised for network-related issues."""

    pass


class StorageError(DownloadError):
    """Exception raised for file system/storage issues."""

    pass


class InsufficientSpaceError(StorageError):
    """Exception raised when there's insufficient disk space."""

    pass


class InvalidFilePathError(StorageError):
    """Exception raised when file path is invalid or unsafe."""

    pass