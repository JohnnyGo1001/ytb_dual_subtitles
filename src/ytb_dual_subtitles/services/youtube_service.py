"""YouTube service for video download operations.

Subtask 1.1: 创建 YouTubeService 类，实现 URL 验证
Subtask 1.2: 实现视频信息获取 (get_video_info)
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qs, urlparse

import yt_dlp

from ytb_dual_subtitles.exceptions.download_errors import VideoNotFoundError


class YouTubeService:
    """Service for YouTube video operations."""

    def __init__(self, browser_for_cookies: str = "chrome", browser_profile: str | None = None) -> None:
        """Initialize YouTube service.

        Args:
            browser_for_cookies: Browser to extract cookies from (chrome, firefox, safari, edge)
            browser_profile: Browser profile name (e.g., 'Default', 'Profile 1'). If None, uses default profile.
        """
        # YouTube URL patterns
        self._youtube_patterns = [
            re.compile(r"^https?://(www\.|m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)"),
            re.compile(r"^https?://(www\.)?youtu\.be/([a-zA-Z0-9_-]+)"),
        ]

        self.browser_for_cookies = browser_for_cookies
        self.browser_profile = browser_profile

    def _get_cookies_config(self) -> dict[str, Any]:
        """Get cookies configuration, trying multiple browsers if needed.

        Returns:
            Dictionary with cookies configuration
        """
        # If browser profile is specified, use it directly
        if self.browser_profile:
            # Format: browser:profile (e.g., "chrome:Default")
            browser_spec = (self.browser_for_cookies, self.browser_profile)
            try:
                # Test if cookies can be extracted with this profile
                import yt_dlp
                test_opts = {
                    'cookiesfrombrowser': browser_spec,
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                }
                with yt_dlp.YoutubeDL(test_opts) as ydl:
                    # If no exception is raised, we can use this browser profile
                    return {'cookiesfrombrowser': browser_spec}
            except Exception as e:
                print(f"Warning: Failed to load cookies from {self.browser_for_cookies}:{self.browser_profile}: {e}")

        # Try different browsers in order of preference (without profile)
        browsers_to_try = [self.browser_for_cookies, 'chrome', 'firefox', 'safari', 'edge']

        for browser in browsers_to_try:
            try:
                # Test if cookies can be extracted from this browser
                import yt_dlp
                test_opts = {
                    'cookiesfrombrowser': (browser,),
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                }
                with yt_dlp.YoutubeDL(test_opts) as ydl:
                    # If no exception is raised, we can use this browser
                    return {'cookiesfrombrowser': (browser,)}
            except Exception:
                continue

        # Fallback: no cookies available
        print("Warning: Could not extract cookies from any browser")
        return {}

    def _get_base_ydl_opts(self) -> dict[str, Any]:
        """Get base yt-dlp options with anti-detection settings.

        Returns:
            Dictionary of yt-dlp options
        """
        base_opts = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'extractor_args': {
                'youtube': {
                    # Use android client first, fallback to web with cookies
                    # android client bypasses signature requirements but doesn't support cookies
                    # web client supports cookies but requires signature solving
                    'player_client': ['android', 'web'],
                    'comment_sort': ['top'],
                    'max_comments': [0],  # Don't extract comments
                }
            },
            # Additional anti-detection measures
            'sleep_interval_requests': 1,
            'sleep_interval_subtitles': 1,
            'quiet': True,
            'no_warnings': True,
        }

        # Add cookies configuration for web client fallback
        # Android client will skip cookies, web client will use them
        cookies_config = self._get_cookies_config()
        base_opts.update(cookies_config)

        return base_opts

    def validate_youtube_url(self, url: str) -> bool:
        """Validate if the URL is a valid YouTube video URL.

        Args:
            url: The URL to validate

        Returns:
            True if URL is valid YouTube video URL, False otherwise
        """
        if not url or not isinstance(url, str):
            return False

        # Check against YouTube URL patterns
        for pattern in self._youtube_patterns:
            if pattern.match(url.strip()):
                return True

        return False

    def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL.

        Args:
            url: YouTube video URL

        Returns:
            Video ID string

        Raises:
            ValueError: If URL is invalid or video ID cannot be extracted
        """
        if not self.validate_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        url = url.strip()

        # Try each pattern to extract video ID
        for pattern in self._youtube_patterns:
            match = pattern.match(url)
            if match:
                return match.group(2)

        # Fallback: parse URL parameters
        parsed_url = urlparse(url)
        if parsed_url.netloc in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
            params = parse_qs(parsed_url.query)
            if "v" in params:
                return params["v"][0]

        raise ValueError("Could not extract video ID from URL")

    def generate_filename_from_url(self, url: str) -> str:
        """Generate filename from YouTube URL path format.

        Args:
            url: YouTube video URL

        Returns:
            Filename in format: watch_v_videoId.mp4

        Raises:
            ValueError: If URL is invalid
        """
        if not self.validate_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        url = url.strip()
        parsed_url = urlparse(url)

        # Handle different YouTube URL formats
        if parsed_url.netloc in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
            # For standard watch URLs: watch?v=videoId -> watch_v_videoId
            if parsed_url.path == "/watch":
                params = parse_qs(parsed_url.query)
                if "v" in params:
                    video_id = params["v"][0]
                    return f"watch_v_{video_id}.mp4"

        elif parsed_url.netloc in ["youtu.be"]:
            # For shortened URLs: youtu.be/videoId -> watch_v_videoId
            video_id = parsed_url.path.lstrip('/')
            if video_id:
                return f"watch_v_{video_id}.mp4"

        # Fallback to extract video ID and use standard format
        try:
            video_id = self.extract_video_id(url)
            return f"watch_v_{video_id}.mp4"
        except ValueError:
            raise ValueError("Could not generate filename from URL")

    async def get_video_info(self, video_id: str) -> dict[str, Any]:
        """Get video information from YouTube.

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary containing video information

        Raises:
            VideoNotFoundError: If video is not found or unavailable
        """
        url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            # Configure yt-dlp for info extraction only
            ydl_opts = self._get_base_ydl_opts()
            ydl_opts.update({
                "extract_flat": False,
            })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Extract relevant information
                return {
                    "id": info.get("id", video_id),
                    "title": info.get("title", "Unknown Title"),
                    "duration": info.get("duration", 0),
                    "uploader": info.get("uploader", "Unknown"),
                    "upload_date": info.get("upload_date"),
                    "view_count": info.get("view_count", 0),
                    "description": info.get("description", ""),
                }

        except yt_dlp.DownloadError as e:
            raise VideoNotFoundError(f"Video {video_id} not found: {e}") from e
        except Exception as e:
            raise VideoNotFoundError(f"Failed to get video info for {video_id}: {e}") from e

    def sanitize_filename(self, title: str, max_length: int = 200) -> str:
        """Sanitize video title for safe filename use.

        Args:
            title: Original video title
            max_length: Maximum filename length

        Returns:
            Sanitized filename safe for file system
        """
        if not title:
            return "untitled"

        # Remove or replace invalid characters with spaces
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, " ", title)

        # Replace multiple spaces with single space
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip()

        return sanitized or "untitled"

    def create_progress_hook(
        self,
        task_id: str,
        progress_callback: Callable[[dict[str, Any]], None]
    ) -> Callable[[dict[str, Any]], None]:
        """Create a progress hook function for yt-dlp.

        Args:
            task_id: Unique identifier for the download task
            progress_callback: Callback function to receive progress updates

        Returns:
            Progress hook function compatible with yt-dlp
        """
        def progress_hook(data: dict[str, Any]) -> None:
            """Progress hook for yt-dlp download progress.

            Args:
                data: Progress data from yt-dlp
            """
            status = data.get('status', 'unknown')

            # Convert yt-dlp progress data to our standard format
            progress_info: dict[str, Any] = {
                'task_id': task_id,
                'type': 'download_progress',
                'status': self._map_yt_dlp_status(status),
            }

            if status == 'downloading':
                downloaded = data.get('downloaded_bytes', 0)
                total = data.get('total_bytes', 0) or data.get('total_bytes_estimate', 0)

                # Calculate percentage
                percentage = 0.0
                if total > 0:
                    percentage = (downloaded / total) * 100.0

                progress_info['progress'] = {
                    'percentage': percentage,
                    'downloaded': downloaded,
                    'total': total,
                    'speed': data.get('speed', 0),
                    'eta': data.get('eta', 0),
                }

            elif status == 'finished':
                progress_info['progress'] = {
                    'percentage': 100.0,
                    'downloaded': data.get('total_bytes', 0),
                    'total': data.get('total_bytes', 0),
                    'speed': 0,
                    'eta': 0,
                }

            elif status == 'error':
                progress_info['error'] = data.get('error', 'Unknown error')

            # Send progress update via callback
            progress_callback(progress_info)

        return progress_hook

    def _map_yt_dlp_status(self, yt_dlp_status: str) -> str:
        """Map yt-dlp status to our internal status format.

        Args:
            yt_dlp_status: Status from yt-dlp

        Returns:
            Mapped status string
        """
        status_mapping = {
            'downloading': 'downloading',
            'finished': 'completed',
            'error': 'error',
            'extracting': 'downloading',  # Treat as downloading
        }

        return status_mapping.get(yt_dlp_status, 'unknown')

    async def download_video(self, url: str, task_id: str, output_path: str | None = None) -> str:
        """Download video using yt-dlp.

        Args:
            url: YouTube video URL
            task_id: Task identifier for progress tracking
            output_path: Optional custom output path

        Returns:
            Path to downloaded video file
        """
        if not self.validate_youtube_url(url):
            raise ValueError("Invalid YouTube URL")

        # Import here to avoid circular imports
        from ytb_dual_subtitles.core.settings import get_settings

        settings = get_settings()

        # Generate output filename
        if output_path:
            output_file = output_path
        else:
            filename = self.generate_filename_from_url(url)
            output_file = str(settings.download_path / filename)

        # For yt-dlp to correctly name subtitle files, we need to provide
        # the output template without extension, so it can add .en.vtt, .zh-CN.vtt, etc.
        from pathlib import Path
        output_path_obj = Path(output_file)
        output_template = str(output_path_obj.parent / output_path_obj.stem)

        # Configure yt-dlp options from settings
        yt_dlp_opts = settings.get_yt_dlp_opts()

        # Configure yt-dlp options
        ydl_opts = self._get_base_ydl_opts()
        ydl_opts.update({
            # Use a flexible format selection that falls back gracefully
            # This selects best video+audio, but will work even if some formats are unavailable
            # Only select actual video formats, not images/storyboards
            'format': '(bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best)[vcodec!=none]',
            'outtmpl': output_template,  # Without extension for proper subtitle naming
            'noplaylist': True,
            'extract_flat': False,
            'writeinfojson': False,
            'writesubtitles': yt_dlp_opts.get('writesubtitles', True),
            'writeautomaticsub': yt_dlp_opts.get('writeautomaticsub', True),
            'subtitleslangs': yt_dlp_opts.get('subtitleslangs', ['en', 'zh-CN', 'zh-Hans']),
            'subtitlesformat': yt_dlp_opts.get('subtitlesformat', 'vtt'),
            'convert_subs': 'vtt',  # Ensure subtitles are converted to VTT format
            'merge_output_format': 'mp4',  # Merge to MP4 format
            # Try to use age-gated bypass
            'age_limit': 99,
            # Force IPv4 to avoid some network issues
            'force_ipv4': True,
            # Add verbose error messages for debugging
            'verbose': False,
        })

        # Allow settings to override format if explicitly specified
        if 'format' in yt_dlp_opts and yt_dlp_opts['format']:
            ydl_opts['format'] = yt_dlp_opts['format']

        try:
            # Use asyncio to run yt-dlp in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()

            def download_sync():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # First, check if video has any downloadable formats
                    info = ydl.extract_info(url, download=False)

                    # Check if there are any actual video formats available
                    formats = info.get('formats', [])
                    video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('vcodec') != 'images']

                    if not video_formats:
                        error_msg = "No video formats available for this video. "
                        if info.get('availability') == 'needs_auth':
                            error_msg += "This video requires authentication (login). Please make sure you're logged into YouTube in your browser."
                        elif info.get('live_status') == 'is_upcoming':
                            error_msg += "This is an upcoming live stream that hasn't started yet."
                        elif info.get('live_status') == 'was_live':
                            error_msg += "This was a live stream. It may not be available for download."
                        elif info.get('availability') in ['premium_only', 'subscriber_only']:
                            error_msg += "This is a premium or members-only video."
                        else:
                            error_msg += "The video may be region-locked, private, or deleted."
                        raise VideoNotFoundError(error_msg)

                    # Proceed with download
                    ydl.download([url])

                # Find the actual downloaded file (yt-dlp adds extension automatically)
                # Try common video extensions
                for ext in ['.mp4', '.webm', '.mkv', '.m4a']:
                    candidate = output_template + ext
                    if Path(candidate).exists():
                        return candidate

                # Check if file exists without extension
                if Path(output_template).exists():
                    # File downloaded without extension, rename it to .mp4
                    target_path = output_template + '.mp4'
                    Path(output_template).rename(target_path)
                    return target_path

                # Fallback to original output_file if nothing found
                return output_file

            # Run in executor to prevent blocking
            result = await loop.run_in_executor(None, download_sync)
            return result

        except VideoNotFoundError:
            # Re-raise our custom errors with clear messages
            raise
        except yt_dlp.DownloadError as e:
            error_str = str(e).lower()
            if 'requested format is not available' in error_str:
                raise VideoNotFoundError(
                    "The video format is not available. This may be due to: "
                    "1) Regional restrictions, 2) Login required, or 3) Video is private/deleted. "
                    "Try logging into YouTube in your browser (Chrome) first."
                ) from e
            elif 'video unavailable' in error_str:
                raise VideoNotFoundError("Video is unavailable or has been removed.") from e
            else:
                raise VideoNotFoundError(f"Failed to download video: {e}") from e
        except Exception as e:
            raise VideoNotFoundError(f"Unexpected error during download: {e}") from e