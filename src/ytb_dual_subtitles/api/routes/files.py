"""File management API routes for YouTube dual-subtitles system.

This module provides endpoints for video list, search, deletion and file operations.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ytb_dual_subtitles.core.database import get_db
from ytb_dual_subtitles.core.settings import get_settings
from ytb_dual_subtitles.models import (
    ApiResponse,
    ErrorCodes,
)
from ytb_dual_subtitles.models.video import Video, VideoStatus, Subtitle
from ytb_dual_subtitles.services.file_service import FileService


router = APIRouter(tags=["files"])


@router.get("/videos", response_model=ApiResponse[dict[str, Any]])
async def get_videos(
    search: str | None = Query(None, description="Search query for video titles"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    status: VideoStatus | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[dict[str, Any]]:
    """Get paginated list of videos with search and filtering.

    Returns:
        Dictionary containing videos list and pagination information
    """
    # Build base query with eager loading of subtitles
    query = select(Video).options(selectinload(Video.subtitles))

    # Apply filters
    conditions = []

    if search:
        # Search in title and file path
        search_term = f"%{search}%"
        conditions.append(
            or_(
                Video.title.ilike(search_term),
                Video.file_path.ilike(search_term)
            )
        )

    if status:
        conditions.append(Video.status == status)

    if conditions:
        query = query.where(and_(*conditions))

    # Apply sorting
    sort_column = getattr(Video, sort_by, Video.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Get total count
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # Execute query
    result = await db.execute(query)
    videos = result.scalars().all()

    # Calculate pagination info
    total_pages = (total + per_page - 1) // per_page

    # Format response
    video_list = []
    for video in videos:
        # Get file size
        file_size = 0
        if video.file_path and Path(video.file_path).exists():
            try:
                file_size = Path(video.file_path).stat().st_size
            except Exception:
                file_size = 0

        video_data = {
            "id": video.id,
            "youtube_id": video.youtube_id,
            "title": video.title,
            "duration": video.duration,
            "file_path": video.file_path,
            "file_size": file_size,
            "status": video.status,
            "created_at": video.created_at.isoformat() if video.created_at else None,
            "updated_at": video.updated_at.isoformat() if video.updated_at else None,
            "thumbnail_url": f"/api/videos/{video.id}/thumbnail/medium",
            "has_subtitles": bool(video.subtitles)
        }
        video_list.append(video_data)

    data = {
        "videos": video_list,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages
        }
    }
    return ApiResponse.success_response(data=data)


@router.delete("/videos/{video_id}", response_model=ApiResponse[dict[str, Any]])
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[dict[str, Any]]:
    """Delete a video and its associated files.

    Args:
        video_id: ID of video to delete

    Returns:
        Unified API response with success message
    """
    # Find video
    query = select(Video).where(Video.id == video_id)
    result = await db.execute(query)
    video = result.scalar_one_or_none()

    if not video:
        return ApiResponse.error_response(
            error_code=ErrorCodes.NOT_FOUND,
            error_msg="Video not found"
        )

    try:
        # Delete physical file
        file_service = FileService(db)
        if video.file_path and Path(video.file_path).exists():
            await file_service.delete_video_file(Path(video.file_path))

        # Delete from database
        await db.delete(video)
        await db.commit()

        data = {
            "message": "Video deleted successfully",
            "video_id": video_id
        }
        return ApiResponse.success_response(data=data)

    except Exception as e:
        await db.rollback()
        return ApiResponse.error_response(
            error_code=ErrorCodes.INTERNAL_ERROR,
            error_msg=f"Failed to delete video: {str(e)}"
        )


@router.get("/videos/{video_id}/thumbnail/{size}")
async def get_thumbnail(
    video_id: int,
    size: str = Path(..., pattern="^(small|medium|large)$"),
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """Get video thumbnail by size.

    Args:
        video_id: ID of video
        size: Thumbnail size (small/medium/large)

    Returns:
        Thumbnail image file

    Raises:
        HTTPException: If video or thumbnail not found
    """
    # Find video
    query = select(Video).where(Video.id == video_id)
    result = await db.execute(query)
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Construct thumbnail path
    settings = get_settings()
    thumbnail_dir = settings.download_path.parent / "thumbnails"

    # Try different formats
    video_name = Path(video.file_path).stem if video.file_path else f"video_{video.id}"

    for ext in ["webp", "jpeg", "jpg"]:
        thumbnail_path = thumbnail_dir / f"{video_name}_{size}.{ext}"
        if thumbnail_path.exists():
            return FileResponse(
                path=thumbnail_path,
                media_type=f"image/{ext}" if ext != "jpg" else "image/jpeg",
                filename=f"{video_name}_{size}.{ext}"
            )

    raise HTTPException(status_code=404, detail="Thumbnail not found")


@router.get("/videos/{video_id}/subtitles/{language}/export")
async def export_subtitles(
    video_id: int,
    language: str,
    format: str = Query("srt", pattern="^(srt|vtt)$"),
    db: AsyncSession = Depends(get_db)
) -> Response:
    """Export video subtitles in specified format.

    Args:
        video_id: ID of video
        language: Subtitle language code
        format: Export format (srt/vtt)

    Returns:
        Subtitle file content

    Raises:
        HTTPException: If video or subtitles not found
    """
    # Find video
    query = select(Video).where(Video.id == video_id)
    result = await db.execute(query)
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Find subtitles
    subtitle_query = select(Subtitle).where(
        and_(
            Subtitle.video_id == video_id,
            Subtitle.language == language
        )
    )
    subtitle_result = await db.execute(subtitle_query)
    subtitle = subtitle_result.scalar_one_or_none()

    if not subtitle:
        raise HTTPException(
            status_code=404,
            detail=f"Subtitles not found for language: {language}"
        )

    # Generate subtitle content
    subtitle_content = await generate_srt_content(subtitle, db)

    # Prepare response
    filename = f"{video.title}_{language}.{format}"

    return Response(
        content=subtitle_content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\""
        }
    )


async def generate_srt_content(subtitle: Subtitle, db: AsyncSession) -> str:
    """Generate SRT format content from subtitle segments.

    Args:
        subtitle: Subtitle instance
        db: Database session

    Returns:
        SRT formatted string
    """
    # This is a placeholder implementation
    # In a real implementation, you would fetch subtitle segments
    # and format them according to SRT specification

    content = []
    content.append("1")
    content.append("00:00:01,000 --> 00:00:05,000")
    content.append("Sample subtitle content")
    content.append("")

    return "\n".join(content)