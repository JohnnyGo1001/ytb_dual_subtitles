"""Database administration utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from ytb_dual_subtitles.core.settings import get_settings
from ytb_dual_subtitles.database.models import DatabaseManager
from ytb_dual_subtitles.database.task_dao import TaskDAO


class DatabaseAdmin:
    """Database administration utilities."""

    def __init__(self) -> None:
        """Initialize database admin."""
        settings = get_settings()
        self.db_manager = DatabaseManager(settings.database_path)
        self.task_dao = TaskDAO(self.db_manager)

    def get_statistics(self) -> dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        stats = self.task_dao.get_task_statistics()

        # Add database file info
        db_path = Path(self.db_manager.db_path)
        if db_path.exists():
            stat_info = db_path.stat()
            stats['database'] = {
                'file_size_bytes': stat_info.st_size,
                'file_size_mb': round(stat_info.st_size / (1024 * 1024), 2),
                'last_modified': stat_info.st_mtime,
                'path': str(db_path)
            }

        return stats

    def cleanup_old_tasks(self, days: int = 30) -> int:
        """Clean up old completed tasks.

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted tasks
        """
        return self.task_dao.cleanup_old_tasks(days)

    def reset_hanging_tasks(self) -> int:
        """Reset tasks stuck in downloading status.

        Returns:
            Number of reset tasks
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE download_tasks
                SET status = 'pending',
                    status_message = 'Reset after service restart'
                WHERE status = 'downloading'
            """)
            conn.commit()
            return cursor.rowcount

    def vacuum_database(self) -> None:
        """Vacuum database to reclaim space."""
        with self.db_manager.get_connection() as conn:
            conn.execute("VACUUM")

    def backup_database(self, backup_path: str | Path) -> None:
        """Create database backup.

        Args:
            backup_path: Path for backup file
        """
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_manager.db_path) as source:
            with sqlite3.connect(backup_path) as backup:
                source.backup(backup)

    def get_table_info(self) -> dict[str, Any]:
        """Get database table information.

        Returns:
            Dictionary with table schemas and row counts
        """
        info = {}

        with self.db_manager.get_connection() as conn:
            # Get table schemas
            cursor = conn.execute("""
                SELECT name, sql FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)

            for table_name, create_sql in cursor.fetchall():
                # Get row count
                count_cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = count_cursor.fetchone()[0]

                # Get column info
                pragma_cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = [
                    {
                        'name': row[1],
                        'type': row[2],
                        'notnull': bool(row[3]),
                        'default_value': row[4],
                        'primary_key': bool(row[5])
                    }
                    for row in pragma_cursor.fetchall()
                ]

                info[table_name] = {
                    'row_count': row_count,
                    'columns': columns,
                    'create_sql': create_sql
                }

        return info


def print_database_status() -> None:
    """Print database status for CLI usage."""
    admin = DatabaseAdmin()

    print("=== YouTube Downloader Database Status ===\n")

    # Statistics
    stats = admin.get_statistics()
    print("Task Statistics:")
    for status, count in stats.items():
        if status != 'database':
            print(f"  {status}: {count}")

    # Database info
    if 'database' in stats:
        db_info = stats['database']
        print(f"\nDatabase Info:")
        print(f"  Path: {db_info['path']}")
        print(f"  Size: {db_info['file_size_mb']} MB")

    # Table info
    table_info = admin.get_table_info()
    print(f"\nTables:")
    for table_name, info in table_info.items():
        print(f"  {table_name}: {info['row_count']} rows")


if __name__ == "__main__":
    print_database_status()