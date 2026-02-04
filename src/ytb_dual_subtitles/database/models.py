"""Database models and table definitions."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class DatabaseManager:
    """SQLite database manager for persistent storage."""

    def __init__(self, db_path: str | Path) -> None:
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Download tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS download_tasks (
                    task_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    error_message TEXT,
                    status_message TEXT,
                    retry_count INTEGER DEFAULT 0,

                    -- File information
                    file_path TEXT,
                    downloaded_bytes INTEGER DEFAULT 0,
                    total_bytes INTEGER DEFAULT 0,
                    download_speed REAL DEFAULT 0.0,
                    eta_seconds INTEGER DEFAULT 0,

                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Video files table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS video_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    file_path TEXT NOT NULL UNIQUE,
                    filename TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    duration REAL DEFAULT 0,
                    format TEXT,
                    quality TEXT,

                    -- Video metadata
                    video_id TEXT,
                    uploader TEXT,
                    upload_date TEXT,
                    view_count INTEGER DEFAULT 0,
                    description TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (task_id) REFERENCES download_tasks(task_id)
                        ON DELETE CASCADE
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON download_tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON download_tasks(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_files_task_id ON video_files(task_id)")

            conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute("PRAGMA foreign_keys = ON")
        return conn