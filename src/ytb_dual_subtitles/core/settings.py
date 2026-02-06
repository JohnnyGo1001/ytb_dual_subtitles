"""Configuration management for YouTube dual-subtitles system.

This module provides environment-based configuration management using Pydantic
for type safety and validation.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support.

    All settings can be overridden via environment variables with YTB_ prefix.
    For example: YTB_DATABASE_URL, YTB_DEBUG, etc.
    """

    model_config = SettingsConfigDict(
        env_prefix="YTB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database configuration
    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{Path.home() / 'ytb' / 'data' / 'ytb.db'}",
        description="Database connection URL"
    )

    # File storage paths
    download_path: Path = Field(
        default=Path.home() / "ytb" / "videos",
        description="Directory for downloaded video files"
    )

    subtitle_path: Path = Field(
        default=Path.home() / "ytb" / "subtitles",
        description="Directory for subtitle files"
    )

    data_path: Path = Field(
        default=Path.home() / "ytb" / "data",
        description="Directory for application data"
    )

    # Browser cookie configuration
    browser_name: str = Field(
        default="chrome",
        description="Browser name for cookie extraction (chrome, firefox, safari, edge)"
    )

    browser_profile: str | None = Field(
        default="Default",
        description="Browser profile name for cookie extraction (e.g., 'Default', 'Profile 1')"
    )

    # Application configuration
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )

    # Download configuration
    max_concurrent_downloads: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of concurrent downloads"
    )

    download_timeout: int = Field(
        default=300,
        ge=30,
        description="Download timeout in seconds"
    )

    download_max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum number of retry attempts for failed downloads"
    )

    # yt-dlp configuration
    yt_dlp_format: str | None = Field(
        default=None,
        description="Custom video format string for yt-dlp. If None, uses smart default format selection."
    )

    yt_dlp_write_subtitles: bool = Field(
        default=True,
        description="Whether to download subtitles"
    )

    yt_dlp_write_auto_subtitles: bool = Field(
        default=True,
        description="Whether to download auto-generated subtitles"
    )

    yt_dlp_subtitle_languages: str = Field(
        default="en,zh-CN,zh-Hans,zh-Hant,zh-TW,ja,ko,es,fr,de",
        description="Comma-separated list of subtitle languages to download"
    )

    yt_dlp_subtitle_format: str = Field(
        default="vtt",
        description="Subtitle format (vtt, srt, ass, etc.)"
    )

    yt_dlp_merge_output_format: str = Field(
        default="mp4",
        description="Container format for merged video+audio (mp4, mkv, webm, etc.)"
    )

    # Web server configuration
    host: str = Field(
        default="127.0.0.1",
        description="Server host address"
    )

    port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Server port"
    )

    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for CORS configuration"
    )

    def __init__(self, **kwargs) -> None:
        """Initialize settings and create necessary directories."""
        super().__init__(**kwargs)
        self._create_directories()

    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.download_path,
            self.subtitle_path,
            self.data_path,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def database_path(self) -> Path:
        """Get the SQLite database file path."""
        if "sqlite" in self.database_url:
            # Extract filename from sqlite URL
            db_file = self.database_url.split("///")[-1]
            # Always use data_path as base directory
            return self.data_path / db_file
        return self.data_path / "ytb.db"

    def get_yt_dlp_opts(self) -> dict[str, any]:
        """Get yt-dlp configuration options from settings.

        Returns:
            Dictionary of yt-dlp options configured via environment variables
        """
        # Parse subtitle languages from comma-separated string
        subtitle_langs = [lang.strip() for lang in self.yt_dlp_subtitle_languages.split(',') if lang.strip()]

        opts = {
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
            'writesubtitles': self.yt_dlp_write_subtitles,
            'writeautomaticsub': self.yt_dlp_write_auto_subtitles,
            'subtitleslangs': subtitle_langs,
            'subtitlesformat': self.yt_dlp_subtitle_format,
            'ignoreerrors': True,
            'no_warnings': not self.debug,
            'extractaudio': False,
            'audioformat': 'mp3',
            'embed_subs': False,  # We handle subtitles separately
            'merge_output_format': self.yt_dlp_merge_output_format,
        }

        # Only add format if explicitly specified
        if self.yt_dlp_format:
            opts['format'] = self.yt_dlp_format

        return opts


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance.

    This function is used for FastAPI dependency injection.
    """
    return settings