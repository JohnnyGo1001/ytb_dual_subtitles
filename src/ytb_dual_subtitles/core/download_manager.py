"""Download manager for handling concurrent video downloads.

Subtask 2.1: 创建 DownloadManager 类，实现任务队列
Subtask 2.2: 实现并发控制（最多3个并行任务）
Subtask 2.3: 实现下载状态管理和状态转换
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any

from ytb_dual_subtitles.exceptions.download_errors import (
    VideoNotFoundError,
)
from ytb_dual_subtitles.models.video import DownloadTaskStatus
from ytb_dual_subtitles.services.youtube_service import YouTubeService
from ytb_dual_subtitles.database.models import DatabaseManager
from ytb_dual_subtitles.database.task_dao import TaskDAO
from ytb_dual_subtitles.core.settings import get_settings


class DownloadTask:
    """Represents a single download task."""

    def __init__(self, url: str) -> None:
        """Initialize download task.

        Args:
            url: YouTube video URL to download
        """
        self.task_id = str(uuid.uuid4())
        self.url = url
        self.status = DownloadTaskStatus.PENDING
        self.progress = 0
        self.error_message: str | None = None
        self.status_message: str = ""
        self.retry_count = 0
        self.created_at = datetime.now()
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None

        # Detailed progress information for HTTP API
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.download_speed = 0.0
        self.eta_seconds = 0
        self.last_updated = datetime.now()

    def update_progress(self, progress: int, message: str = "", **kwargs) -> None:
        """Update task progress.

        Args:
            progress: Progress percentage (0-100)
            message: Status message
            **kwargs: Additional progress data (downloaded, total, speed, eta)
        """
        self.progress = progress
        self.status_message = message
        self.last_updated = datetime.now()

        # Store detailed progress data for HTTP API
        self.downloaded_bytes = kwargs.get("downloaded", 0)
        self.total_bytes = kwargs.get("total", 0)
        self.download_speed = kwargs.get("speed", 0.0)
        self.eta_seconds = kwargs.get("eta", 0)

    def set_error(self, error_message: str) -> None:
        """Set task error status.

        Args:
            error_message: Error description
        """
        self.status = DownloadTaskStatus.ERROR
        self.error_message = error_message


class DownloadManager:
    """Manages concurrent video download tasks."""

    def __init__(
        self,
        youtube_service: YouTubeService,
        storage_service: Any,  # Will be properly typed when storage service is implemented
        max_concurrent: int = 3,
        max_retries: int = 3
    ) -> None:
        """Initialize download manager.

        Args:
            youtube_service: YouTube service for video operations
            storage_service: Storage service for file operations
            max_concurrent: Maximum number of concurrent downloads
        """
        self._youtube_service = youtube_service
        self._storage_service = storage_service
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries

        # Database setup
        settings = get_settings()
        self._db_manager = DatabaseManager(settings.database_path)
        self._task_dao = TaskDAO(self._db_manager)

        # Concurrency control
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running_tasks: dict[str, asyncio.Task[None]] = {}

        # Load active tasks from database on startup
        self._restore_active_tasks()

    def _restore_active_tasks(self) -> None:
        """Restore active tasks from database on startup."""
        # Mark any hanging 'downloading' tasks as pending to retry
        pending_tasks = self._task_dao.get_tasks_by_status('downloading')
        for task_data in pending_tasks:
            self._task_dao.update_task(task_data['task_id'], {
                'status': 'pending',
                'status_message': 'Restored after service restart'
            })

    def _task_data_to_download_task(self, task_data: dict[str, Any]) -> DownloadTask:
        """Convert database task data to DownloadTask object.

        Args:
            task_data: Task data from database

        Returns:
            DownloadTask object
        """
        task = DownloadTask(task_data['url'])
        task.task_id = task_data['task_id']
        task.status = DownloadTaskStatus(task_data['status'])
        task.progress = task_data['progress']
        task.error_message = task_data['error_message']
        task.status_message = task_data['status_message'] or ''
        task.retry_count = task_data['retry_count']

        # Parse timestamps
        if task_data['created_at']:
            task.created_at = datetime.fromisoformat(task_data['created_at'])
        if task_data['started_at']:
            task.started_at = datetime.fromisoformat(task_data['started_at'])
        if task_data['completed_at']:
            task.completed_at = datetime.fromisoformat(task_data['completed_at'])
        if task_data['last_updated']:
            task.last_updated = datetime.fromisoformat(task_data['last_updated'])

        # File info
        task.downloaded_bytes = task_data['downloaded_bytes']
        task.total_bytes = task_data['total_bytes']
        task.download_speed = task_data['download_speed']
        task.eta_seconds = task_data['eta_seconds']

        return task

    def _download_task_to_data(self, task: DownloadTask) -> dict[str, Any]:
        """Convert DownloadTask object to database data.

        Args:
            task: DownloadTask object

        Returns:
            Dictionary for database storage
        """
        return {
            'task_id': task.task_id,
            'url': task.url,
            'title': getattr(task, 'title', None),
            'status': task.status.value,
            'progress': task.progress,
            'error_message': task.error_message,
            'status_message': task.status_message,
            'retry_count': task.retry_count,
            'downloaded_bytes': task.downloaded_bytes,
            'total_bytes': task.total_bytes,
            'download_speed': task.download_speed,
            'eta_seconds': task.eta_seconds,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'last_updated': task.last_updated.isoformat() if task.last_updated else None,
        }

    async def create_task(self, url: str) -> DownloadTask:
        """Create a new download task with duplicate check.

        Args:
            url: YouTube video URL

        Returns:
            Created download task or existing active task for same URL

        Raises:
            ValueError: If URL is invalid
        """
        # Check if there's already an active task for this URL in database
        normalized_url = url.strip()
        existing_task_data = self._task_dao.get_active_task_by_url(normalized_url)
        if existing_task_data:
            return self._task_data_to_download_task(existing_task_data)

        # Get video info to extract title for deduplication
        try:
            video_id = self._youtube_service.extract_video_id(url)
            video_info = await self._youtube_service.get_video_info(video_id)
            video_title = video_info.get("title", "")
        except Exception as e:
            # Create task but mark it as errored if we can't get video info
            task = DownloadTask(url=url)
            task.set_error(f"Failed to get video info: {e}")
            # Save to database
            task_data = self._download_task_to_data(task)
            self._task_dao.create_task(task_data)
            return task

        # Check if video with same title already exists (deduplication by title)
        if video_title:
            existing_task_by_title = self._task_dao.get_completed_task_by_title(video_title)
            if existing_task_by_title:
                # Video with same title already downloaded
                existing_task = self._task_data_to_download_task(existing_task_by_title)
                return existing_task

        # Generate filename from URL
        try:
            filename = self._youtube_service.generate_filename_from_url(url)
            file_path = self._storage_service.generate_file_path_from_url(filename)
        except ValueError as e:
            # Create task but mark it as errored if URL is invalid
            task = DownloadTask(url=url)
            task.set_error(f"Invalid URL: {e}")
            # Save to database
            task_data = self._download_task_to_data(task)
            self._task_dao.create_task(task_data)
            return task

        # Check if file already exists
        existing_info = self._storage_service.get_existing_file_info(file_path)
        if existing_info:
            # File exists, create a completed task with existing file info
            task = DownloadTask(url=url)
            task.status = DownloadTaskStatus.COMPLETED
            task.progress = 100
            task.status_message = "File already exists"
            task.completed_at = task.created_at
            task.total_bytes = existing_info.get("size", 0)
            task.downloaded_bytes = existing_info.get("size", 0)
            # Store video title
            setattr(task, 'title', video_title)
            # Save to database
            task_data = self._download_task_to_data(task)
            self._task_dao.create_task(task_data)
            return task

        # File doesn't exist, create normal pending task
        task = DownloadTask(url=url)
        # Store video title in task for later use
        setattr(task, 'title', video_title)
        # Save to database
        task_data = self._download_task_to_data(task)
        self._task_dao.create_task(task_data)
        return task

    async def start_task(self, task_id: str) -> None:
        """Start a download task.

        Args:
            task_id: ID of the task to start

        Raises:
            ValueError: If task is not found
        """
        # Find task in database
        task_data = self._task_dao.get_task(task_id)
        if not task_data:
            raise ValueError("Task not found")

        if task_data['status'] not in ['pending']:
            raise ValueError(f"Task {task_id} is not in pending status")

        # Update status to downloading
        self._task_dao.update_task(task_id, {
            'status': 'downloading',
            'started_at': datetime.now().isoformat()
        })

        # Convert to DownloadTask object for processing
        task = self._task_data_to_download_task(task_data)
        task.status = DownloadTaskStatus.DOWNLOADING
        task.started_at = datetime.now()

        # Start download in background
        download_coro = self._download_task(task)
        self._running_tasks[task_id] = asyncio.create_task(download_coro)

    async def _download_task(self, task: DownloadTask) -> None:
        """Execute the download for a task with retry mechanism.

        Complete workflow:
        1. Download video (0-60% progress)
        2. Process and import subtitles (60-80% progress)
        3. Generate and embed dual subtitles (80-100% progress)

        Args:
            task: Download task to execute
        """
        try:
            async with self._semaphore:
                # Fetch video info first to get title
                try:
                    video_id = self._youtube_service.extract_video_id(task.url)
                    video_info = await self._youtube_service.get_video_info(video_id)
                    title = video_info.get("title", "未知标题")

                    # Update task with title immediately
                    self._task_dao.update_task(task.task_id, {
                        'title': title,
                        'status_message': f'正在下载: {title}',
                        'progress': 0
                    })
                except Exception as e:
                    print(f"Failed to get video info, continuing with download: {e}")
                    title = "未知标题"

                while True:
                    try:
                        # Step 1: Download video (0-60% progress)
                        filename = self._youtube_service.generate_filename_from_url(task.url)
                        file_path = self._storage_service.generate_file_path_from_url(filename)

                        self._task_dao.update_task(task.task_id, {
                            'status_message': f'下载视频中: {title}',
                            'progress': 10
                        })

                        await self._youtube_service.download_video(task.url, task.task_id, str(file_path))

                        # Video download complete
                        self._task_dao.update_task(task.task_id, {
                            'status_message': f'视频下载完成，处理字幕中...',
                            'progress': 60
                        })

                        # Step 2: Process subtitles (already handled in _complete_task)
                        # This will be done in _complete_task -> _create_video_record -> _import_subtitles

                        # Complete task with subtitle processing
                        await self._complete_task(task, success=True)
                        return  # Success, exit retry loop

                    except asyncio.CancelledError:
                        # Task was cancelled, don't mark as error
                        return

                    except Exception as e:
                        # Check if this is a non-retryable error
                        if self._is_non_retryable_error(e):
                            task.set_error(str(e))
                            await self._complete_task(task, success=False)
                            return

                        # If we've exceeded max retries, mark as failed
                        if task.retry_count >= self.max_retries:
                            task.set_error(str(e))
                            await self._complete_task(task, success=False)
                            return

                        # Increment retry count and update database
                        task.retry_count += 1
                        self._task_dao.update_task(task.task_id, {
                            'retry_count': task.retry_count,
                            'status_message': f'Retrying... (attempt {task.retry_count + 1})'
                        })

                        # Wait before retry (exponential backoff)
                        wait_time = 2 ** (task.retry_count - 1)  # 1, 2, 4, 8 seconds
                        await asyncio.sleep(wait_time)

        except asyncio.CancelledError:
            # Task was cancelled, this is expected
            pass

        finally:
            # Clean up running task reference
            if task.task_id in self._running_tasks:
                del self._running_tasks[task.task_id]

    def _is_non_retryable_error(self, error: Exception) -> bool:
        """Check if an error should not trigger retries.

        Args:
            error: Exception that occurred

        Returns:
            True if error should not be retried
        """
        # Don't retry on video not found or similar permanent errors
        non_retryable_types = (VideoNotFoundError,)

        return isinstance(error, non_retryable_types)

    async def _complete_task(self, task: DownloadTask, success: bool) -> None:
        """Complete a download task.

        Args:
            task: DownloadTask object
            success: Whether the task completed successfully
        """
        # Update task status
        if success and task.status != DownloadTaskStatus.ERROR:
            # Video download successful, now process subtitles
            # Update progress to 70% - subtitle import in progress
            self._task_dao.update_task(task.task_id, {
                'status_message': '导入字幕中...',
                'progress': 70
            })

            # Create video record and import subtitles
            video_id = await self._create_video_record(task)

            if video_id:
                # Step 3: Generate and embed dual subtitles (80-100% progress)
                self._task_dao.update_task(task.task_id, {
                    'status_message': '生成双语字幕中...',
                    'progress': 80
                })

                # Process dual subtitles
                await self._process_dual_subtitles(video_id, task)

            task.status = DownloadTaskStatus.COMPLETED
            task.progress = 100

        elif task.status != DownloadTaskStatus.ERROR:
            task.status = DownloadTaskStatus.FAILED

        task.completed_at = datetime.now()

        # Update database
        updates = {
            'status': task.status.value,
            'progress': task.progress,
            'completed_at': task.completed_at.isoformat(),
            'error_message': task.error_message,
            'status_message': '下载完成' if success else task.error_message
        }

        self._task_dao.update_task(task.task_id, updates)

        # Clean up running task reference
        if task.task_id in self._running_tasks:
            del self._running_tasks[task.task_id]

    async def _create_video_record(self, task: DownloadTask) -> int | None:
        """Create a video record in the videos table after successful download.

        Args:
            task: Completed download task

        Returns:
            Video ID if successful, None otherwise
        """
        try:
            # Extract video ID from URL
            video_id = self._youtube_service.extract_video_id(task.url)

            # Get video information
            video_info = await self._youtube_service.get_video_info(video_id)

            # Get downloaded file path
            filename = self._youtube_service.generate_filename_from_url(task.url)
            file_path = self._storage_service.generate_file_path_from_url(filename)

            # Import SQLAlchemy components
            from ytb_dual_subtitles.core.database import get_db_session
            from ytb_dual_subtitles.models.video import Video, VideoStatus

            # Create video record in the videos table
            async with get_db_session() as session:
                # Check if video already exists by youtube_id or title
                from sqlalchemy import select, or_
                video_title = video_info.get("title", "未知标题")

                existing_video = await session.execute(
                    select(Video).where(
                        or_(
                            Video.youtube_id == video_id,
                            Video.title == video_title
                        )
                    )
                )
                existing = existing_video.scalar_one_or_none()
                if existing:
                    print(f"Video '{video_title}' already exists in database (ID: {existing.youtube_id}), skipping creation")
                    # Update download task with title
                    self._task_dao.update_task(task.task_id, {
                        'title': video_title
                    })
                    return existing.id

                # Create new video record
                video = Video(
                    youtube_id=video_id,
                    title=video_title,
                    description=video_info.get("description", ""),
                    duration=video_info.get("duration", 0),
                    file_path=str(file_path),
                    status=VideoStatus.COMPLETED,
                )

                session.add(video)
                await session.commit()
                await session.refresh(video)  # Refresh to get the ID
                print(f"Created video record for: {video_title} (ID: {video.id})")

                # Process and import subtitles
                await self._import_subtitles(video, file_path, session)

                # Update download task with title
                self._task_dao.update_task(task.task_id, {
                    'title': video_title
                })

                return video.id

        except Exception as e:
            print(f"Failed to create video record: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _import_subtitles(self, video: Any, video_path: str, session: Any) -> None:
        """Import subtitle files downloaded by yt-dlp.

        Args:
            video: Video record from database
            video_path: Path to the video file
            session: Database session
        """
        try:
            from pathlib import Path
            from ytb_dual_subtitles.models.video import Subtitle, SubtitleSegment, SubtitleSourceType

            video_path_obj = Path(video_path)
            base_path = video_path_obj.parent
            base_name = video_path_obj.stem

            # Find all subtitle files (yt-dlp names them like: video.en.vtt, video.zh-CN.vtt)
            subtitle_files = list(base_path.glob(f"{base_name}.*.vtt"))

            if not subtitle_files:
                print(f"No subtitle files found for: {base_name}")
                return

            for subtitle_file in subtitle_files:
                try:
                    # Extract language from filename (e.g., "video.en.vtt" -> "en")
                    parts = subtitle_file.stem.split('.')
                    if len(parts) < 2:
                        continue
                    language = parts[-1]

                    # Map language codes to display names
                    language_map = {
                        'en': 'English',
                        'zh-Hans': '简体中文',
                        'zh-Hant': '繁體中文',
                        'zh-CN': '简体中文',
                        'zh-TW': '繁體中文',
                        'ja': '日本語',
                        'ko': '한국어',
                        'es': 'Español',
                        'fr': 'Français',
                        'de': 'Deutsch',
                    }
                    language_name = language_map.get(language, language)

                    # Parse VTT file
                    segments = await self._parse_vtt_file(subtitle_file)

                    if not segments:
                        print(f"No segments found in: {subtitle_file}")
                        continue

                    # Create subtitle record
                    subtitle = Subtitle(
                        video_id=video.id,
                        language=language,
                        language_name=language_name,
                        source_type=SubtitleSourceType.YOUTUBE
                    )
                    session.add(subtitle)
                    await session.flush()  # Get subtitle ID

                    # Create subtitle segments
                    for seq, seg in enumerate(segments, start=1):
                        segment = SubtitleSegment(
                            subtitle_id=subtitle.id,
                            sequence=seq,
                            start_time=seg['start'],
                            end_time=seg['end'],
                            text=seg['text']
                        )
                        session.add(segment)

                    await session.commit()
                    print(f"Imported {len(segments)} subtitle segments for language: {language}")

                except Exception as e:
                    print(f"Failed to import subtitle {subtitle_file}: {e}")
                    await session.rollback()
                    continue

        except Exception as e:
            print(f"Failed to import subtitles: {e}")

    async def _parse_vtt_file(self, vtt_path: Path) -> list[dict[str, Any]]:
        """Parse WebVTT subtitle file.

        Args:
            vtt_path: Path to VTT file

        Returns:
            List of subtitle segments with start, end, and text
        """
        import re

        segments = []

        try:
            with open(vtt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # WebVTT format: timestamp --> timestamp followed by text
            # Example:
            # 00:00:00.000 --> 00:00:03.500
            # Hello, welcome to this tutorial.

            # Split by double newlines to get blocks
            blocks = re.split(r'\n\n+', content)

            for block in blocks:
                # Skip WEBVTT header and empty blocks
                if not block.strip() or block.strip().startswith('WEBVTT') or block.strip().startswith('NOTE'):
                    continue

                lines = block.strip().split('\n')

                # Find the timestamp line
                timestamp_line = None
                text_lines = []

                for line in lines:
                    if '-->' in line:
                        timestamp_line = line
                    elif timestamp_line:  # After timestamp, it's text
                        # Remove VTT formatting tags like <c>, </c>
                        clean_line = re.sub(r'<[^>]+>', '', line)
                        if clean_line.strip():
                            text_lines.append(clean_line.strip())

                if timestamp_line and text_lines:
                    # Parse timestamps
                    match = re.match(r'([\d:\.]+)\s*-->\s*([\d:\.]+)', timestamp_line)
                    if match:
                        start_str = match.group(1)
                        end_str = match.group(2)

                        # Convert timestamp to seconds
                        start_time = self._timestamp_to_seconds(start_str)
                        end_time = self._timestamp_to_seconds(end_str)

                        segments.append({
                            'start': start_time,
                            'end': end_time,
                            'text': ' '.join(text_lines)
                        })

            return segments

        except Exception as e:
            print(f"Error parsing VTT file {vtt_path}: {e}")
            return []

    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert VTT timestamp to seconds.

        Args:
            timestamp: Timestamp string (e.g., "00:01:30.500" or "01:30.500")

        Returns:
            Time in seconds
        """
        parts = timestamp.split(':')

        if len(parts) == 3:  # HH:MM:SS.mmm
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # MM:SS.mmm
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:  # SS.mmm
            return float(parts[0])

    async def _process_dual_subtitles(self, video_id: int, task: DownloadTask) -> None:
        """Generate and embed dual subtitles into video.

        Args:
            video_id: Database ID of the video
            task: Download task for progress tracking
        """
        try:
            import subprocess
            from pathlib import Path
            from datetime import timedelta
            from sqlalchemy import select
            from ytb_dual_subtitles.core.database import get_db_session
            from ytb_dual_subtitles.models.video import Video, Subtitle, SubtitleSegment

            print(f"Processing dual subtitles for video ID: {video_id}")

            # Get video record
            async with get_db_session() as session:
                video = await session.get(Video, video_id)
                if not video or not video.file_path:
                    print(f"Video {video_id} not found or has no file path")
                    return

                video_path = Path(video.file_path)
                if not video_path.exists():
                    print(f"Video file not found: {video_path}")
                    return

                # Check if we have both zh-CN and en subtitles
                stmt = select(Subtitle).where(Subtitle.video_id == video_id)
                result = await session.execute(stmt)
                subtitles = result.scalars().all()

                languages = {sub.language for sub in subtitles}
                if 'zh-CN' not in languages or 'en' not in languages:
                    print(f"Missing required subtitles (need zh-CN and en), found: {languages}")
                    self._task_dao.update_task(task.task_id, {
                        'status_message': '缺少必需的字幕语言',
                        'progress': 100
                    })
                    return

                # Update progress
                self._task_dao.update_task(task.task_id, {
                    'status_message': '生成双语字幕文件...',
                    'progress': 85
                })

                # Generate dual subtitle SRT file
                settings = get_settings()
                subtitle_dir = settings.subtitle_path / str(video_id)
                subtitle_dir.mkdir(parents=True, exist_ok=True)
                subtitle_path = subtitle_dir / f"{video.youtube_id}_dual.srt"

                # Get Chinese and English subtitles
                zh_subtitle = next((s for s in subtitles if s.language == 'zh-CN'), None)
                en_subtitle = next((s for s in subtitles if s.language == 'en'), None)

                # Get segments
                stmt_zh = select(SubtitleSegment).where(
                    SubtitleSegment.subtitle_id == zh_subtitle.id
                ).order_by(SubtitleSegment.sequence)
                result_zh = await session.execute(stmt_zh)
                zh_segments = result_zh.scalars().all()

                stmt_en = select(SubtitleSegment).where(
                    SubtitleSegment.subtitle_id == en_subtitle.id
                ).order_by(SubtitleSegment.sequence)
                result_en = await session.execute(stmt_en)
                en_segments = result_en.scalars().all()

                # Generate dual SRT file
                await self._generate_dual_srt(zh_segments, en_segments, subtitle_path)

                print(f"Generated dual subtitle file: {subtitle_path}")

                # Update progress
                self._task_dao.update_task(task.task_id, {
                    'status_message': '嵌入字幕到视频...',
                    'progress': 90
                })

                # Embed subtitles into video
                output_path = video_path.parent / f"{video_path.stem}_with_subs{video_path.suffix}"

                cmd = [
                    'ffmpeg',
                    '-i', str(video_path),
                    '-i', str(subtitle_path),
                    '-c', 'copy',
                    '-c:s', 'mov_text',
                    '-metadata:s:s:0', 'language=chi',
                    '-metadata:s:s:0', 'title=双语字幕',
                    '-y',
                    str(output_path)
                ]

                print(f"Embedding subtitles with command: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    print(f"FFmpeg failed: {result.stderr}")
                    self._task_dao.update_task(task.task_id, {
                        'status_message': 'FFmpeg 嵌入字幕失败',
                        'progress': 100
                    })
                    return

                if output_path.exists():
                    print(f"Dual subtitle video created: {output_path}")
                    self._task_dao.update_task(task.task_id, {
                        'status_message': '双语字幕处理完成',
                        'progress': 100
                    })
                else:
                    print(f"Output file not created: {output_path}")

        except Exception as e:
            print(f"Failed to process dual subtitles: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail the entire download task
            self._task_dao.update_task(task.task_id, {
                'status_message': f'双语字幕处理失败: {str(e)}',
                'progress': 100
            })

    async def _generate_dual_srt(
        self,
        zh_segments: list,
        en_segments: list,
        output_path: Path
    ) -> None:
        """Generate dual language SRT file.

        Args:
            zh_segments: Chinese subtitle segments
            en_segments: English subtitle segments
            output_path: Output SRT file path
        """
        from datetime import timedelta

        def format_srt_time(seconds: float) -> str:
            """Convert seconds to SRT time format."""
            td = timedelta(seconds=seconds)
            total_seconds = int(td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60
            millis = int((seconds - int(seconds)) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

        # Align subtitles by time
        dual_segments = []
        for zh_seg in zh_segments:
            # Find best matching English segment
            best_match = None
            min_time_diff = float('inf')

            for en_seg in en_segments:
                time_diff = abs(en_seg.start_time - zh_seg.start_time)
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    best_match = en_seg

            dual_segments.append({
                'start': zh_seg.start_time,
                'end': zh_seg.end_time,
                'zh': zh_seg.text.strip(),
                'en': best_match.text.strip() if best_match else ''
            })

        # Write SRT file
        with open(output_path, 'w', encoding='utf-8') as f:
            for idx, segment in enumerate(dual_segments, start=1):
                f.write(f"{idx}\n")
                f.write(f"{format_srt_time(segment['start'])} --> {format_srt_time(segment['end'])}\n")
                f.write(f"{segment['zh']}\n")
                if segment['en']:
                    f.write(f"{segment['en']}\n")
                f.write("\n")

    def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """Get status of a download task.

        Args:
            task_id: ID of the task

        Returns:
            Task status information or None if not found
        """
        # Get task from database
        task_data = self._task_dao.get_task(task_id)
        if not task_data:
            return None

        return {
            'task_id': task_data['task_id'],
            'url': task_data['url'],
            'title': task_data.get('title') or '未知标题',  # Include title with fallback
            'status': task_data['status'],
            'progress': task_data['progress'],
            'status_message': task_data['status_message'] or '',
            'error_message': task_data['error_message'],
            'created_at': task_data['created_at'],
            'started_at': task_data['started_at'],
            'completed_at': task_data['completed_at'],
            'last_updated': task_data['last_updated'],
            'downloaded_bytes': task_data['downloaded_bytes'],
            'total_bytes': task_data['total_bytes'],
            'download_speed': task_data['download_speed'],
            'eta_seconds': task_data['eta_seconds'],
        }

    def list_tasks(self) -> list[dict[str, Any]]:
        """List all tasks.

        Returns:
            List of task status information
        """
        # Get all tasks from database
        all_task_data = self._task_dao.get_all_tasks()


        tasks = []
        for task_data in all_task_data:
            # Convert to the format expected by the API
            task_status = {
                'task_id': task_data['task_id'],
                'url': task_data['url'],
                'title': task_data.get('title') or '未知标题',  # Include title with fallback
                'status': task_data['status'],
                'progress': task_data['progress'],
                'status_message': task_data['status_message'] or '',
                'error_message': task_data['error_message'],
                'created_at': task_data['created_at'],
                'started_at': task_data['started_at'],
                'completed_at': task_data['completed_at'],
                'last_updated': task_data['last_updated'],
                'downloaded_bytes': task_data['downloaded_bytes'],
                'total_bytes': task_data['total_bytes'],
                'download_speed': task_data['download_speed'],
                'eta_seconds': task_data['eta_seconds'],
            }
            tasks.append(task_status)

        return tasks


    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a download task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            True if task was found and cancelled, False otherwise
        """
        # Get task from database
        task_data = self._task_dao.get_task(task_id)
        if not task_data:
            return False

        # Can only cancel pending or downloading tasks
        if task_data['status'] not in ['pending', 'downloading']:
            return False

        # If it's currently running, cancel the asyncio task
        if task_id in self._running_tasks:
            running_task = self._running_tasks[task_id]
            running_task.cancel()
            try:
                await running_task
            except asyncio.CancelledError:
                pass  # Expected cancellation
            finally:
                # Clean up running task reference
                if task_id in self._running_tasks:
                    del self._running_tasks[task_id]

        # Update task status in database
        updates = {
            'status': 'cancelled',
            'completed_at': datetime.now().isoformat(),
            'status_message': 'Cancelled by user'
        }

        success = self._task_dao.update_task(task_id, updates)

        # Clean up temporary files if needed
        if hasattr(self._storage_service, 'cleanup_temp_files'):
            cleanup_func = self._storage_service.cleanup_temp_files
            if asyncio.iscoroutinefunction(cleanup_func):
                await cleanup_func(task_id)
            else:
                cleanup_func(task_id)

        return success