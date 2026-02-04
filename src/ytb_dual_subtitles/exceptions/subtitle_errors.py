"""Subtitle-related exceptions.

Task 1: 字幕提取服务开发 - 异常类定义
"""

from __future__ import annotations


class SubtitleError(Exception):
    """Base exception for subtitle-related errors."""

    def __init__(self, message: str) -> None:
        """Initialize subtitle error.

        Args:
            message: Error message
        """
        self.message = message
        super().__init__(message)


class SubtitleNotFoundError(SubtitleError):
    """Exception raised when subtitles are not found for a video."""

    pass


class SubtitleFormatError(SubtitleError):
    """Exception raised when subtitle format is invalid or unsupported."""

    pass


class TranslationError(SubtitleError):
    """Exception raised when translation service fails."""

    pass


class SubtitleExtractionError(SubtitleError):
    """Exception raised when subtitle extraction fails."""

    pass

class SubtitleDataError(Exception):
    """字幕数据处理相关异常"""
    pass
