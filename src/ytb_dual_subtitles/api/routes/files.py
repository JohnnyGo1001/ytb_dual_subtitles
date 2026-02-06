"""File management API routes for YouTube dual-subtitles system.

This module provides endpoints for video list, search, deletion and file operations.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam, Query, Response
from fastapi.responses import FileResponse, RedirectResponse
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
    category: str | None = Query(None, description="Filter by category"),
    group_by_category: bool = Query(False, description="Group videos by category"),
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

    if category:
        conditions.append(Video.category == category)

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
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # Execute query
    result = await db.execute(query)
    videos = result.scalars().all()

    # Calculate pagination info
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

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

        # Check if dual subtitles version exists
        has_dual_subs = False
        if video.file_path:
            original_path = Path(video.file_path)
            dual_subs_path = original_path.parent / f"{original_path.stem}_with_subs{original_path.suffix}"
            has_dual_subs = dual_subs_path.exists()

        video_data = {
            "id": video.id,
            "youtube_id": video.youtube_id,
            "title": video.title,
            "duration": video.duration,
            "file_path": video.file_path,
            "file_size": file_size,
            "status": video.status,
            "category": video.category or "未分类",
            "channel_name": video.channel_name,
            "created_at": video.created_at.isoformat() if video.created_at else None,
            "updated_at": video.updated_at.isoformat() if video.updated_at else None,
            "thumbnail_url": f"/api/videos/{video.id}/thumbnail/medium",
            "has_subtitles": bool(video.subtitles),
            "has_dual_subs": has_dual_subs  # Indicate if dual subtitles version exists
        }
        video_list.append(video_data)

    # Group by category if requested
    if group_by_category:
        categories = {}
        for video_data in video_list:
            cat = video_data["category"] or "未分类"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(video_data)

        data = {
            "categories": categories,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        }
    else:
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


@router.get("/videos/categories", response_model=ApiResponse[dict[str, Any]])
async def get_categories(
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[dict[str, Any]]:
    """Get all video categories with video counts.

    Returns:
        Dictionary containing categories and their video counts
    """
    try:
        # Query to get category counts
        query = select(
            Video.category,
            func.count(Video.id).label('count')
        ).group_by(Video.category).order_by(func.count(Video.id).desc())

        result = await db.execute(query)
        categories_data = result.all()

        categories = []
        for category, count in categories_data:
            categories.append({
                "name": category or "未分类",
                "count": count
            })

        data = {
            "categories": categories,
            "total": len(categories)
        }
        return ApiResponse.success_response(data=data)

    except Exception as e:
        return ApiResponse.error_response(
            error_code=ErrorCodes.INTERNAL_ERROR,
            error_msg=f"Failed to get categories: {str(e)}"
        )


@router.get("/videos/{video_id}", response_model=ApiResponse[dict[str, Any]])
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[dict[str, Any]]:
    """Get a single video by ID.

    Args:
        video_id: ID of video to retrieve

    Returns:
        Unified API response with video data
    """
    # Find video with subtitles
    query = select(Video).options(selectinload(Video.subtitles)).where(Video.id == video_id)
    result = await db.execute(query)
    video = result.scalar_one_or_none()

    if not video:
        return ApiResponse.error_response(
            error_code=ErrorCodes.NOT_FOUND,
            error_msg="Video not found"
        )

    # Get file size
    file_size = 0
    if video.file_path and Path(video.file_path).exists():
        try:
            file_size = Path(video.file_path).stat().st_size
        except Exception:
            file_size = 0

    # Check if dual subtitles version exists
    has_dual_subs = False
    if video.file_path:
        original_path = Path(video.file_path)
        dual_subs_path = original_path.parent / f"{original_path.stem}_with_subs{original_path.suffix}"
        has_dual_subs = dual_subs_path.exists()

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
        "download_url": f"/api/videos/{video.id}/stream",  # Add download URL for video player
        "has_subtitles": bool(video.subtitles),
        "has_dual_subs": has_dual_subs,  # Indicate if dual subtitles version exists
        "subtitles": [
            {
                "id": sub.id,
                "language": sub.language,
                "language_name": sub.language_name,
            }
            for sub in video.subtitles
        ] if video.subtitles else []
    }
    return ApiResponse.success_response(data=video_data)


@router.patch("/videos/{video_id}/category", response_model=ApiResponse[dict[str, Any]])
async def update_video_category(
    video_id: int,
    category: str,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[dict[str, Any]]:
    """Update video category.

    Args:
        video_id: ID of video to update
        category: New category name

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
        # Update category
        video.category = category
        await db.commit()

        data = {
            "message": "Video category updated successfully",
            "video_id": video_id,
            "category": category
        }
        return ApiResponse.success_response(data=data)

    except Exception as e:
        await db.rollback()
        return ApiResponse.error_response(
            error_code=ErrorCodes.INTERNAL_ERROR,
            error_msg=f"Failed to update video category: {str(e)}"
        )


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


@router.get("/videos/{video_id}/stream")
async def stream_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """Stream video file.

    Args:
        video_id: ID of video to stream

    Returns:
        Video file for streaming (prioritizes version with dual subtitles)

    Raises:
        HTTPException: If video not found or file doesn't exist
    """
    # Find video
    query = select(Video).where(Video.id == video_id)
    result = await db.execute(query)
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if not video.file_path or not Path(video.file_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    # Check if version with dual subtitles exists
    original_path = Path(video.file_path)
    dual_subs_path = original_path.parent / f"{original_path.stem}_with_subs{original_path.suffix}"

    # Prefer dual subtitles version if it exists
    if dual_subs_path.exists():
        video_path = dual_subs_path
    else:
        video_path = original_path

    # Return video file
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=video_path.name
    )


@router.get("/subtitles/{video_id}", response_model=ApiResponse[dict[str, Any]])
async def get_subtitles(
    video_id: int,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[dict[str, Any]]:
    """Get subtitle segments for a video with dual language support.

    Args:
        video_id: ID of video

    Returns:
        Unified API response with subtitle segments
    """
    # Find video with subtitles
    query = select(Video).options(selectinload(Video.subtitles)).where(Video.id == video_id)
    result = await db.execute(query)
    video = result.scalar_one_or_none()

    if not video:
        return ApiResponse.error_response(
            error_code=ErrorCodes.NOT_FOUND,
            error_msg="Video not found"
        )

    if not video.subtitles:
        return ApiResponse.success_response(data={
            "video_id": str(video_id),
            "segments": [],
            "language_original": "en",
        })

    # Find English and Chinese subtitles
    english_sub = None
    chinese_sub = None

    for sub in video.subtitles:
        if sub.language == 'en':
            english_sub = sub
        elif sub.language in ['zh-CN', 'zh-Hans', 'zh']:
            chinese_sub = sub

    # Get English subtitle segments
    english_segments = []
    if english_sub:
        from ytb_dual_subtitles.models.video import SubtitleSegment
        segments_query = select(SubtitleSegment).where(
            SubtitleSegment.subtitle_id == english_sub.id
        ).order_by(SubtitleSegment.sequence)

        segments_result = await db.execute(segments_query)
        english_segments = segments_result.scalars().all()

    # Get Chinese subtitle segments
    chinese_segments_dict = {}
    if chinese_sub:
        from ytb_dual_subtitles.models.video import SubtitleSegment
        segments_query = select(SubtitleSegment).where(
            SubtitleSegment.subtitle_id == chinese_sub.id
        ).order_by(SubtitleSegment.sequence)

        segments_result = await db.execute(segments_query)
        chinese_segments = segments_result.scalars().all()

        # Create lookup dict by sequence for matching
        for seg in chinese_segments:
            chinese_segments_dict[seg.sequence] = seg

    # Combine segments
    combined_segments = []
    for seg in english_segments:
        chinese_text = None
        if seg.sequence in chinese_segments_dict:
            chinese_text = chinese_segments_dict[seg.sequence].text

        combined_segments.append({
            "id": str(seg.id),
            "video_id": str(video_id),
            "start_time": seg.start_time,
            "end_time": seg.end_time,
            "text_english": seg.text,
            "text_chinese": chinese_text,
            "sequence": seg.sequence,
        })

    subtitle_data = {
        "video_id": str(video_id),
        "segments": combined_segments,
        "language_original": "en",
        "language_translated": "zh-CN" if chinese_sub else None,
    }

    return ApiResponse.success_response(data=subtitle_data)


@router.get("/videos/{video_id}/thumbnail/{size}", response_class=Response)
async def get_thumbnail(
    video_id: int,
    size: str = PathParam(..., pattern="^(small|medium|large)$"),
    db: AsyncSession = Depends(get_db)
):
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

    # If local thumbnail not found and video has YouTube ID, redirect to YouTube thumbnail
    if video.youtube_id:
        # Map size to YouTube thumbnail quality
        quality_map = {
            "small": "default",      # 120x90
            "medium": "mqdefault",   # 320x180
            "large": "hqdefault"     # 480x360
        }
        quality = quality_map.get(size, "mqdefault")
        youtube_thumbnail_url = f"https://img.youtube.com/vi/{video.youtube_id}/{quality}.jpg"
        return RedirectResponse(url=youtube_thumbnail_url)

    raise HTTPException(status_code=404, detail="Thumbnail not found")


@router.get("/subtitles/{video_id}/dual.vtt")
async def get_dual_subtitle_vtt(
    video_id: int,
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """Get dual subtitle VTT file for web player.

    Args:
        video_id: ID of video

    Returns:
        WebVTT subtitle file with dual language (Chinese + English)

    Raises:
        HTTPException: If video or subtitle file not found
    """
    # Find video
    query = select(Video).where(Video.id == video_id)
    result = await db.execute(query)
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Construct VTT path
    settings = get_settings()
    vtt_path = settings.subtitle_path / str(video_id) / f"{video.youtube_id}_dual.vtt"

    if not vtt_path.exists():
        # Try to find any dual vtt file
        dual_vtt_files = list((settings.subtitle_path / str(video_id)).glob("*_dual.vtt"))
        if dual_vtt_files:
            vtt_path = dual_vtt_files[0]
        else:
            raise HTTPException(status_code=404, detail="Dual subtitle file not found")

    return FileResponse(
        path=str(vtt_path),
        media_type="text/vtt",
        filename=f"{video.youtube_id}_dual.vtt"
    )


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