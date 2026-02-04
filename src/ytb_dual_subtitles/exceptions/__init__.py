"""Download-related exceptions package."""

from .download_errors import (
    DownloadError,
    NetworkError,
    StorageError,
    VideoNotFoundError,
)

__all__ = [
    "DownloadError",
    "NetworkError",
    "StorageError",
    "VideoNotFoundError",
]