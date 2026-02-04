"""File synchronization and monitoring tasks.

This module provides scheduled tasks for file system monitoring and cleanup.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from ytb_dual_subtitles.core.settings import get_settings
from ytb_dual_subtitles.services.file_service import FileService
from ytb_dual_subtitles.services.metadata_service import MetadataService
from ytb_dual_subtitles.services.storage_management import StorageManagementService

logger = logging.getLogger(__name__)


class FileSyncTaskManager:
    """Manager for file synchronization and monitoring tasks."""

    def __init__(self, db_session_factory: Callable[[], AsyncSession]) -> None:
        """Initialize task manager.

        Args:
            db_session_factory: Factory function to create database sessions
        """
        self.db_session_factory = db_session_factory
        self.settings = get_settings()
        self.running_tasks: dict[str, asyncio.Task] = {}
        self._stop_event = asyncio.Event()

    async def start_all_tasks(self) -> None:
        """Start all scheduled tasks."""
        logger.info("Starting file sync tasks")

        # Start file scanning task
        self.running_tasks["file_scan"] = asyncio.create_task(
            self._run_periodic_file_scan()
        )

        # Start metadata generation task
        self.running_tasks["metadata_gen"] = asyncio.create_task(
            self._run_metadata_generation_task()
        )

        # Start cleanup task
        self.running_tasks["cleanup"] = asyncio.create_task(
            self._run_periodic_cleanup()
        )

        # Start integrity check task
        self.running_tasks["integrity_check"] = asyncio.create_task(
            self._run_integrity_check_task()
        )

        logger.info(f"Started {len(self.running_tasks)} file sync tasks")

    async def stop_all_tasks(self) -> None:
        """Stop all running tasks."""
        logger.info("Stopping file sync tasks")

        # Signal all tasks to stop
        self._stop_event.set()

        # Cancel all running tasks
        for task_name, task in self.running_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Cancelled task: {task_name}")

        self.running_tasks.clear()
        logger.info("All file sync tasks stopped")

    async def _run_periodic_file_scan(self) -> None:
        """Run periodic file scanning task."""
        scan_interval = 300  # 5 minutes
        full_sync_interval = 3600  # 1 hour
        last_full_sync = datetime.min

        while not self._stop_event.is_set():
            try:
                async with self.db_session_factory() as session:
                    file_service = FileService(db_session=session)
                    download_path = self.settings.download_path

                    now = datetime.now()
                    should_full_sync = (now - last_full_sync).seconds >= full_sync_interval

                    if should_full_sync:
                        logger.info("Starting full file synchronization")
                        sync_result = await file_service.full_sync(download_path)
                        last_full_sync = now
                        logger.info(
                            f"Full sync completed: {sync_result.new_files} new, "
                            f"{sync_result.missing_files} missing, "
                            f"{sync_result.integrity_checked_files} checked"
                        )
                    else:
                        logger.debug("Starting incremental file scan")
                        await file_service.incremental_scan(download_path)

            except Exception as e:
                logger.error(f"Error in file scan task: {e}")

            # Wait for next scan or stop event
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=scan_interval)
                break  # Stop event was set
            except asyncio.TimeoutError:
                continue  # Continue with next scan

    async def _run_metadata_generation_task(self) -> None:
        """Run metadata generation task for videos without metadata."""
        check_interval = 600  # 10 minutes
        batch_size = 5

        while not self._stop_event.is_set():
            try:
                async with self.db_session_factory() as session:
                    metadata_service = MetadataService()

                    # Find videos without metadata (simplified - in real implementation
                    # you'd query database for videos missing metadata)
                    download_path = self.settings.download_path
                    video_files = []

                    for file_path in download_path.glob("*.mp4"):
                        video_files.append(file_path)
                        if len(video_files) >= batch_size:
                            break

                    if video_files:
                        logger.info(f"Generating metadata for {len(video_files)} videos")
                        results = await metadata_service.extract_batch_metadata(video_files)
                        logger.info(f"Generated metadata for {len(results)} videos")

                        # Generate thumbnails for videos
                        thumbnail_dir = self.settings.download_path.parent / "thumbnails"
                        for file_path in video_files[:3]:  # Limit to 3 per batch
                            try:
                                await metadata_service.generate_thumbnails(
                                    file_path, thumbnail_dir
                                )
                            except Exception as e:
                                logger.error(f"Failed to generate thumbnails for {file_path}: {e}")

            except Exception as e:
                logger.error(f"Error in metadata generation task: {e}")

            # Wait for next check
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=check_interval)
                break
            except asyncio.TimeoutError:
                continue

    async def _run_periodic_cleanup(self) -> None:
        """Run periodic storage cleanup task."""
        # Run daily at 2 AM (simplified schedule)
        cleanup_interval = 86400  # 24 hours

        while not self._stop_event.is_set():
            try:
                async with self.db_session_factory() as session:
                    storage_service = StorageManagementService(db_session=session)

                    # Check storage quota
                    quota_status = await storage_service.check_storage_quota()
                    logger.info(f"Storage status: {quota_status['status']} ({quota_status['usage_percentage']:.1f}%)")

                    # Run auto cleanup if needed
                    if quota_status.get("auto_cleanup_needed", False):
                        logger.info("Running automatic cleanup due to high storage usage")

                        # Clean temp files
                        temp_cleaned, temp_space = await storage_service.clean_temp_files()
                        if temp_cleaned > 0:
                            logger.info(f"Cleaned {temp_cleaned} temp files, freed {temp_space} bytes")

                        # Clean orphaned thumbnails
                        thumb_cleaned, thumb_space = await storage_service.clean_orphaned_thumbnails()
                        if thumb_cleaned > 0:
                            logger.info(f"Cleaned {thumb_cleaned} orphaned thumbnails, freed {thumb_space} bytes")

                    # Generate cleanup suggestions
                    suggestions = await storage_service.analyze_cleanup_suggestions()
                    if suggestions:
                        total_space = sum(s.space_saved for s in suggestions)
                        logger.info(f"Found {len(suggestions)} cleanup suggestions, {total_space} bytes potential savings")

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

            # Wait for next cleanup cycle
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=cleanup_interval)
                break
            except asyncio.TimeoutError:
                continue

    async def _run_integrity_check_task(self) -> None:
        """Run periodic integrity check task."""
        check_interval = 7200  # 2 hours

        while not self._stop_event.is_set():
            try:
                async with self.db_session_factory() as session:
                    file_service = FileService(db_session=session)

                    # Run database repair for missing files
                    repaired_count = await file_service.repair_database_records()
                    if repaired_count > 0:
                        logger.info(f"Repaired {repaired_count} database records")

            except Exception as e:
                logger.error(f"Error in integrity check task: {e}")

            # Wait for next check
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=check_interval)
                break
            except asyncio.TimeoutError:
                continue

    def get_task_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all running tasks.

        Returns:
            Dictionary with task status information
        """
        status = {}
        for task_name, task in self.running_tasks.items():
            status[task_name] = {
                "running": not task.done(),
                "cancelled": task.cancelled() if task.done() else False,
                "exception": str(task.exception()) if task.done() and task.exception() else None
            }

        return status


# Global task manager instance
_task_manager: FileSyncTaskManager | None = None


def get_task_manager(db_session_factory: Callable[[], AsyncSession]) -> FileSyncTaskManager:
    """Get the global task manager instance.

    Args:
        db_session_factory: Database session factory

    Returns:
        Global task manager instance
    """
    global _task_manager
    if _task_manager is None:
        _task_manager = FileSyncTaskManager(db_session_factory)
    return _task_manager


async def start_background_tasks(db_session_factory: Callable[[], AsyncSession]) -> None:
    """Start all background file sync tasks.

    Args:
        db_session_factory: Database session factory
    """
    task_manager = get_task_manager(db_session_factory)
    await task_manager.start_all_tasks()


async def stop_background_tasks() -> None:
    """Stop all background file sync tasks."""
    global _task_manager
    if _task_manager is not None:
        await _task_manager.stop_all_tasks()


async def get_background_task_status() -> dict[str, dict[str, Any]]:
    """Get status of all background tasks.

    Returns:
        Dictionary with task status information
    """
    global _task_manager
    if _task_manager is not None:
        return _task_manager.get_task_status()
    return {}