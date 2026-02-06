"""Download API routes.

Subtask 3.1-3.6: 下载 API 接口开发
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from ytb_dual_subtitles.core.download_manager import DownloadManager
from ytb_dual_subtitles.core.settings import get_settings
from ytb_dual_subtitles.models import (
    ApiResponse,
    DictResponse,
    ErrorCodes,
    ListResponse,
    StringResponse,
)
from ytb_dual_subtitles.services.youtube_service import YouTubeService
from ytb_dual_subtitles.services.storage_service import StorageService


# Request/Response models
class CreateDownloadRequest(BaseModel):
    """Request model for creating download task."""

    url: str = Field(..., description="YouTube video URL to download")


class DownloadTaskData(BaseModel):
    """Download task data model."""

    task_id: str
    url: str
    status: str
    progress: int = 0
    message: str = ""


class TaskListData(BaseModel):
    """Task list data model."""

    tasks: list[dict[str, Any]]
    total: int


# Router instance
router = APIRouter()

# Singleton instance to maintain state across requests
_download_manager_instance: DownloadManager | None = None


def get_download_manager() -> DownloadManager:
    """Get download manager instance.

    This is a placeholder dependency that will be properly configured
    when the application is fully set up.
    """
    global _download_manager_instance

    # Create singleton instance if it doesn't exist
    if _download_manager_instance is None:
        settings = get_settings()
        youtube_service = YouTubeService(
            browser_for_cookies=settings.browser_name,
            browser_profile=settings.browser_profile
        )
        storage_service = StorageService()
        _download_manager_instance = DownloadManager(
            youtube_service=youtube_service,
            storage_service=storage_service,
            max_concurrent=settings.max_concurrent_downloads,
            max_retries=settings.download_max_retries
        )

    return _download_manager_instance


@router.post("/downloads", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[DownloadTaskData])
async def create_download_task(
    request: CreateDownloadRequest,
    download_manager: DownloadManager = Depends(get_download_manager)
) -> ApiResponse[DownloadTaskData]:
    """Create a new download task.

    Args:
        request: Download task creation request
        download_manager: Download manager instance

    Returns:
        Unified API response with created task information
    """
    # Validate YouTube URL
    settings = get_settings()
    youtube_service = YouTubeService(
        browser_for_cookies=settings.browser_name,
        browser_profile=settings.browser_profile
    )
    if not youtube_service.validate_youtube_url(request.url):
        return ApiResponse.error_response(
            error_code=ErrorCodes.INVALID_URL,
            error_msg="Invalid YouTube URL format"
        )

    try:
        # Create download task
        task = await download_manager.create_task(request.url)

        # Only start the task if it's in pending status
        if task.status.value == 'pending':
            await download_manager.start_task(task.task_id)

        # The create_task method already handles duplicates, so we don't need additional checking
        message = "Task created successfully"

        task_data = DownloadTaskData(
            task_id=task.task_id,
            url=task.url,
            status=task.status.value,
            progress=task.progress,
            message=message
        )

        return ApiResponse.success_response(data=task_data)

    except Exception as e:
        return ApiResponse.error_response(
            error_code=ErrorCodes.DOWNLOAD_FAILED,
            error_msg=f"Failed to create download task: {str(e)}"
        )


@router.get("/downloads/{task_id}", response_model=ApiResponse[DownloadTaskData])
async def get_download_task_status(
    task_id: str,
    download_manager: DownloadManager = Depends(get_download_manager)
) -> ApiResponse[DownloadTaskData]:
    """Get download task status.

    Args:
        task_id: ID of the download task
        download_manager: Download manager instance

    Returns:
        Unified API response with task status information
    """
    task_status = download_manager.get_task_status(task_id)

    if task_status is None:
        return ApiResponse.error_response(
            error_code=ErrorCodes.TASK_NOT_FOUND,
            error_msg="Task not found"
        )

    task_data = DownloadTaskData(
        task_id=task_status["task_id"],
        url=task_status["url"],
        status=task_status["status"],
        progress=task_status["progress"],
        message=task_status.get("status_message", "")
    )

    return ApiResponse.success_response(data=task_data)


@router.get("/list/downloads", response_model=ApiResponse[list[dict[str, Any]]])
async def list_download_tasks(
    limit: int = Query(2, ge=1, le=100, description="Maximum number of tasks to return"),
    download_manager: DownloadManager = Depends(get_download_manager)
) -> ApiResponse[list[dict[str, Any]]]:
    """List recent download tasks, sorted by creation time (newest first).

    Args:
        limit: Maximum number of tasks to return (default: 2)
        download_manager: Download manager instance

    Returns:
        Unified API response with list of recent tasks, including download times
    """
    tasks = download_manager.list_tasks()

    # Sort by created_at in descending order (newest first)
    tasks.sort(key=lambda x: x.get('created_at') or '', reverse=True)

    # Limit to specified number of tasks
    tasks = tasks[:limit]

    return ApiResponse.success_response(data=tasks)


@router.delete("/downloads/{task_id}", response_model=ApiResponse[str])
async def cancel_download_task(
    task_id: str,
    download_manager: DownloadManager = Depends(get_download_manager)
) -> ApiResponse[str]:
    """Cancel a download task.

    Args:
        task_id: ID of the download task to cancel
        download_manager: Download manager instance

    Returns:
        Unified API response with cancellation result
    """
    success = await download_manager.cancel_task(task_id)

    if not success:
        return ApiResponse.error_response(
            error_code=ErrorCodes.TASK_NOT_FOUND,
            error_msg="Task not found or cannot be cancelled"
        )

    return ApiResponse.success_response(data="Task cancelled successfully")


@router.get("/status", response_model=ApiResponse[list[dict[str, Any]]])
async def get_all_tasks_status(
    download_manager: DownloadManager = Depends(get_download_manager)
) -> ApiResponse[list[dict[str, Any]]]:
    """Get status of all tasks for polling.

    Args:
        download_manager: Download manager instance

    Returns:
        Unified API response with list of all task statuses
    """
    tasks = download_manager.list_tasks()
    return ApiResponse.success_response(data=tasks)


@router.get("/status/{task_id}", response_model=ApiResponse[dict[str, Any]])
async def get_task_status_polling(
    task_id: str,
    download_manager: DownloadManager = Depends(get_download_manager)
) -> ApiResponse[dict[str, Any]]:
    """Get specific task status for polling.

    Args:
        task_id: ID of the download task
        download_manager: Download manager instance

    Returns:
        Unified API response with detailed task status
    """
    task_status = download_manager.get_task_status(task_id)

    if task_status is None:
        return ApiResponse.error_response(
            error_code=ErrorCodes.TASK_NOT_FOUND,
            error_msg="Task not found"
        )

    return ApiResponse.success_response(data=task_status)