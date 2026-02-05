"""Category management API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ytb_dual_subtitles.core.database import get_db
from ytb_dual_subtitles.models import ApiResponse, ErrorCodes
from ytb_dual_subtitles.models.video import Video
from pydantic import BaseModel

router = APIRouter(tags=["categories"])


class CategoryCreate(BaseModel):
    """Category creation request."""
    name: str
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    """Category update request."""
    name: str | None = None
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    sort_order: int | None = None


@router.get("/categories", response_model=ApiResponse[dict[str, Any]])
async def get_categories(
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[dict[str, Any]]:
    """Get all categories with video counts.

    Returns:
        List of categories with their properties and video counts
    """
    try:
        import sqlite3
        from pathlib import Path

        # Use raw SQL for now since we're using sqlite3 directly
        db_path = Path.home() / "ytb" / "data" / "ytb.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get categories
        cursor.execute("""
            SELECT c.id, c.name, c.description, c.color, c.icon,
                   c.sort_order, c.is_system,
                   COUNT(DISTINCT v.id) as video_count
            FROM categories c
            LEFT JOIN videos v ON v.category = c.name
            GROUP BY c.id, c.name, c.description, c.color, c.icon, c.sort_order, c.is_system
            ORDER BY c.sort_order, c.name
        """)

        categories_data = cursor.fetchall()
        conn.close()

        categories = []
        for cat_id, name, desc, color, icon, sort_order, is_system, video_count in categories_data:
            categories.append({
                "id": cat_id,
                "name": name,
                "description": desc,
                "color": color,
                "icon": icon,
                "sort_order": sort_order,
                "is_system": bool(is_system),
                "video_count": video_count
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


@router.post("/categories", response_model=ApiResponse[dict[str, Any]])
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[dict[str, Any]]:
    """Create a new category.

    Args:
        category: Category data

    Returns:
        Created category information
    """
    try:
        import sqlite3
        from pathlib import Path

        db_path = Path.home() / "ytb" / "data" / "ytb.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if category already exists
        cursor.execute("SELECT id FROM categories WHERE name = ?", (category.name,))
        if cursor.fetchone():
            conn.close()
            return ApiResponse.error_response(
                error_code=ErrorCodes.VALIDATION_ERROR,
                error_msg=f"Category '{category.name}' already exists"
            )

        # Insert new category
        cursor.execute("""
            INSERT INTO categories (name, description, color, icon, sort_order, is_system)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (category.name, category.description, category.color, category.icon, category.sort_order))

        category_id = cursor.lastrowid
        conn.commit()
        conn.close()

        data = {
            "id": category_id,
            "name": category.name,
            "description": category.description,
            "color": category.color,
            "icon": category.icon,
            "sort_order": category.sort_order,
            "message": "Category created successfully"
        }
        return ApiResponse.success_response(data=data)

    except Exception as e:
        return ApiResponse.error_response(
            error_code=ErrorCodes.INTERNAL_ERROR,
            error_msg=f"Failed to create category: {str(e)}"
        )


@router.patch("/categories/{category_id}", response_model=ApiResponse[dict[str, Any]])
async def update_category(
    category_id: int,
    category: CategoryUpdate,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[dict[str, Any]]:
    """Update a category.

    Args:
        category_id: Category ID
        category: Updated category data

    Returns:
        Updated category information
    """
    try:
        import sqlite3
        from pathlib import Path

        db_path = Path.home() / "ytb" / "data" / "ytb.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if category exists
        cursor.execute("SELECT name, is_system FROM categories WHERE id = ?", (category_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return ApiResponse.error_response(
                error_code=ErrorCodes.NOT_FOUND,
                error_msg="Category not found"
            )

        old_name, is_system = result

        # Build update query
        updates = []
        params = []

        if category.name is not None:
            # Check if new name already exists
            cursor.execute("SELECT id FROM categories WHERE name = ? AND id != ?",
                          (category.name, category_id))
            if cursor.fetchone():
                conn.close()
                return ApiResponse.error_response(
                    error_code=ErrorCodes.VALIDATION_ERROR,
                    error_msg=f"Category '{category.name}' already exists"
                )
            updates.append("name = ?")
            params.append(category.name)

            # Update videos that use this category
            cursor.execute("UPDATE videos SET category = ? WHERE category = ?",
                          (category.name, old_name))

        if category.description is not None:
            updates.append("description = ?")
            params.append(category.description)

        if category.color is not None:
            updates.append("color = ?")
            params.append(category.color)

        if category.icon is not None:
            updates.append("icon = ?")
            params.append(category.icon)

        if category.sort_order is not None:
            updates.append("sort_order = ?")
            params.append(category.sort_order)

        if not updates:
            conn.close()
            return ApiResponse.error_response(
                error_code=ErrorCodes.VALIDATION_ERROR,
                error_msg="No fields to update"
            )

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(category_id)

        query = f"UPDATE categories SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()

        data = {
            "id": category_id,
            "message": "Category updated successfully"
        }
        return ApiResponse.success_response(data=data)

    except Exception as e:
        return ApiResponse.error_response(
            error_code=ErrorCodes.INTERNAL_ERROR,
            error_msg=f"Failed to update category: {str(e)}"
        )


@router.delete("/categories/{category_id}", response_model=ApiResponse[dict[str, Any]])
async def delete_category(
    category_id: int,
    move_to_category: str = "未分类",
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[dict[str, Any]]:
    """Delete a category and move its videos to another category.

    Args:
        category_id: Category ID to delete
        move_to_category: Category name to move videos to (default: "未分类")

    Returns:
        Deletion confirmation
    """
    try:
        import sqlite3
        from pathlib import Path

        db_path = Path.home() / "ytb" / "data" / "ytb.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if category exists
        cursor.execute("SELECT name, is_system FROM categories WHERE id = ?", (category_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return ApiResponse.error_response(
                error_code=ErrorCodes.NOT_FOUND,
                error_msg="Category not found"
            )

        category_name, is_system = result

        # Cannot delete system categories
        if is_system:
            conn.close()
            return ApiResponse.error_response(
                error_code=ErrorCodes.VALIDATION_ERROR,
                error_msg="Cannot delete system category"
            )

        # Move videos to the target category
        cursor.execute("UPDATE videos SET category = ? WHERE category = ?",
                      (move_to_category, category_name))
        moved_count = cursor.rowcount

        # Delete the category
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))

        conn.commit()
        conn.close()

        data = {
            "message": "Category deleted successfully",
            "moved_videos": moved_count,
            "moved_to": move_to_category
        }
        return ApiResponse.success_response(data=data)

    except Exception as e:
        return ApiResponse.error_response(
            error_code=ErrorCodes.INTERNAL_ERROR,
            error_msg=f"Failed to delete category: {str(e)}"
        )
