"""Data Access Object for download tasks."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from ytb_dual_subtitles.database.models import DatabaseManager
from ytb_dual_subtitles.models.video import DownloadTaskStatus


class TaskDAO:
    """Data Access Object for download tasks."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize task DAO.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    def create_task(self, task_data: dict[str, Any]) -> str:
        """Create a new download task.

        Args:
            task_data: Task data dictionary

        Returns:
            Task ID of created task
        """
        with self.db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO download_tasks (
                    task_id, url, title, status, progress, error_message,
                    status_message, retry_count, file_path, downloaded_bytes,
                    total_bytes, download_speed, eta_seconds, created_at,
                    started_at, completed_at, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_data.get('task_id'),
                task_data.get('url'),
                task_data.get('title'),
                task_data.get('status', 'pending'),
                task_data.get('progress', 0),
                task_data.get('error_message'),
                task_data.get('status_message', ''),
                task_data.get('retry_count', 0),
                task_data.get('file_path'),
                task_data.get('downloaded_bytes', 0),
                task_data.get('total_bytes', 0),
                task_data.get('download_speed', 0.0),
                task_data.get('eta_seconds', 0),
                task_data.get('created_at', datetime.now().isoformat()),
                task_data.get('started_at'),
                task_data.get('completed_at'),
                task_data.get('last_updated', datetime.now().isoformat())
            ))
            conn.commit()
            return task_data['task_id']

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task data dictionary or None if not found
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM download_tasks WHERE task_id = ?",
                (task_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def update_task(self, task_id: str, updates: dict[str, Any]) -> bool:
        """Update task fields.

        Args:
            task_id: Task ID
            updates: Dictionary of fields to update

        Returns:
            True if task was updated, False if not found
        """
        if not updates:
            return False

        # Always update last_updated timestamp
        updates['last_updated'] = datetime.now().isoformat()

        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        for field, value in updates.items():
            set_clauses.append(f"{field} = ?")
            values.append(value)

        values.append(task_id)  # For WHERE clause

        query = f"""
            UPDATE download_tasks
            SET {', '.join(set_clauses)}
            WHERE task_id = ?
        """

        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0

    def get_tasks_by_status(self, status: str) -> list[dict[str, Any]]:
        """Get all tasks with specific status.

        Args:
            status: Task status

        Returns:
            List of task data dictionaries
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM download_tasks WHERE status = ? ORDER BY created_at DESC",
                (status,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_all_tasks(self) -> list[dict[str, Any]]:
        """Get all tasks.

        Returns:
            List of task data dictionaries
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM download_tasks ORDER BY created_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete_task(self, task_id: str) -> bool:
        """Delete task by ID.

        Args:
            task_id: Task ID

        Returns:
            True if task was deleted, False if not found
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM download_tasks WHERE task_id = ?",
                (task_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_active_task_by_url(self, url: str) -> dict[str, Any] | None:
        """Get active task (pending or downloading) by URL.

        Args:
            url: Video URL

        Returns:
            Task data dictionary or None if not found
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM download_tasks
                WHERE url = ? AND status IN ('pending', 'downloading', 'processing')
                ORDER BY created_at DESC
                LIMIT 1
            """, (url,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_completed_task_by_title(self, title: str) -> dict[str, Any] | None:
        """Get completed task by video title.

        Args:
            title: Video title

        Returns:
            Task data dictionary or None if not found
        """
        if not title:
            return None

        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM download_tasks
                WHERE title = ? AND status = 'completed'
                ORDER BY created_at DESC
                LIMIT 1
            """, (title,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def cleanup_old_tasks(self, days: int = 30) -> int:
        """Clean up old completed/failed tasks.

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted tasks
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM download_tasks
                WHERE status IN ('completed', 'failed', 'cancelled', 'error')
                AND datetime(created_at) < datetime('now', '-' || ? || ' days')
            """, (days,))
            conn.commit()
            return cursor.rowcount

    def get_task_statistics(self) -> dict[str, Any]:
        """Get task statistics.

        Returns:
            Dictionary with task count by status
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM download_tasks
                GROUP BY status
            """)
            stats = {}
            for row in cursor.fetchall():
                stats[row['status']] = row['count']

            # Total count
            cursor = conn.execute("SELECT COUNT(*) as total FROM download_tasks")
            stats['total'] = cursor.fetchone()['total']

            return stats