"""Error handling and logging utilities.

Task 6: 异常处理和日志记录
Subtasks 6.2-6.4: Error formatting, logging, and performance monitoring
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any


class ErrorResponseFormatter:
    """统一错误响应格式处理器 (Subtask 6.2).

    提供标准化的错误响应格式，确保API返回一致的错误结构。
    """

    @staticmethod
    def format_error(
        error_type: str,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int = 500
    ) -> dict[str, Any]:
        """格式化错误响应为标准格式.

        Args:
            error_type: 错误类型
            message: 错误消息
            details: 错误详细信息
            status_code: HTTP状态码

        Returns:
            标准化的错误响应格式
        """
        return {
            "success": False,
            "error": {
                "type": error_type,
                "message": message,
                "details": details or {},
                "timestamp": datetime.now().isoformat(),
                "status_code": status_code
            }
        }

    @classmethod
    def format_validation_error(cls, field: str, message: str) -> dict[str, Any]:
        """格式化验证错误."""
        return cls.format_error(
            error_type="ValidationError",
            message=f"Validation failed for field '{field}': {message}",
            details={"field": field, "validation_message": message},
            status_code=400
        )

    @classmethod
    def format_download_error(cls, task_id: str, message: str) -> dict[str, Any]:
        """格式化下载错误."""
        return cls.format_error(
            error_type="DownloadError",
            message=message,
            details={"task_id": task_id},
            status_code=422
        )

    @classmethod
    def format_storage_error(cls, file_path: str, message: str) -> dict[str, Any]:
        """格式化存储错误."""
        return cls.format_error(
            error_type="StorageError",
            message=message,
            details={"file_path": file_path},
            status_code=507
        )


class DownloadLogger:
    """下载关键节点日志记录器 (Subtask 6.3).

    记录下载生命周期中的关键事件，便于问题诊断和监控。
    """

    def __init__(self) -> None:
        """Initialize download logger."""
        self.logger = logging.getLogger("ytb_dual_subtitles.download")

    def log_download_start(
        self,
        task_id: str,
        url: str = "",
        title: str = "",
        video_id: str = ""
    ) -> None:
        """记录下载开始."""
        self.logger.info(
            "Download started for task %s",
            task_id,
            extra={
                "task_id": task_id,
                "url": url,
                "title": title,
                "video_id": video_id,
                "event": "download_start"
            }
        )

    def log_download_progress(
        self,
        task_id: str,
        percentage: float,
        speed: int,
        eta: int = 0
    ) -> None:
        """记录下载进度."""
        self.logger.debug(
            "Download progress for task %s: %.1f%% at %d B/s",
            task_id, percentage, speed,
            extra={
                "task_id": task_id,
                "percentage": percentage,
                "speed": speed,
                "eta": eta,
                "event": "download_progress"
            }
        )

    def log_download_complete(
        self,
        task_id: str,
        file_path: str,
        file_size: int,
        duration: float = 0
    ) -> None:
        """记录下载完成."""
        self.logger.info(
            "Download completed for task %s: %s (%d bytes in %.2fs)",
            task_id, file_path, file_size, duration,
            extra={
                "task_id": task_id,
                "file_path": file_path,
                "file_size": file_size,
                "duration": duration,
                "event": "download_complete"
            }
        )

    def log_download_error(
        self,
        task_id: str,
        error: str,
        retry_count: int = 0,
        will_retry: bool = False
    ) -> None:
        """记录下载错误."""
        self.logger.error(
            "Download error for task %s (retry %d): %s",
            task_id, retry_count, error,
            extra={
                "task_id": task_id,
                "error": error,
                "retry_count": retry_count,
                "will_retry": will_retry,
                "event": "download_error"
            }
        )

    def log_download_cancelled(self, task_id: str, reason: str = "") -> None:
        """记录下载取消."""
        self.logger.info(
            "Download cancelled for task %s: %s",
            task_id, reason,
            extra={
                "task_id": task_id,
                "reason": reason,
                "event": "download_cancelled"
            }
        )

    def log_download_retry(self, task_id: str, retry_count: int, delay: float) -> None:
        """记录下载重试."""
        self.logger.info(
            "Download retry %d for task %s after %.2fs",
            retry_count, task_id, delay,
            extra={
                "task_id": task_id,
                "retry_count": retry_count,
                "delay": delay,
                "event": "download_retry"
            }
        )


class PerformanceLogger:
    """性能监控指标收集器 (Subtask 6.4).

    收集和记录系统性能指标，用于监控和优化。
    """

    def __init__(self) -> None:
        """Initialize performance logger."""
        self.logger = logging.getLogger("ytb_dual_subtitles.performance")
        self._operation_times: dict[str, float] = {}

    def log_operation(self, operation_name: str, duration: float) -> None:
        """记录操作耗时.

        Args:
            operation_name: 操作名称
            duration: 操作耗时(秒)
        """
        self.logger.info(
            "Operation '%s' completed in %.3fs",
            operation_name, duration,
            extra={
                "operation": operation_name,
                "duration": duration,
                "event": "performance_metric"
            }
        )

    def start_operation(self, operation_name: str) -> None:
        """开始记录操作耗时."""
        self._operation_times[operation_name] = time.time()

    def end_operation(self, operation_name: str) -> float:
        """结束记录操作耗时，返回耗时."""
        if operation_name not in self._operation_times:
            return 0.0

        start_time = self._operation_times.pop(operation_name)
        duration = time.time() - start_time
        self.log_operation(operation_name, duration)
        return duration

    def log_memory_usage(self, process_name: str, memory_mb: float) -> None:
        """记录内存使用."""
        self.logger.info(
            "Memory usage for %s: %.1f MB",
            process_name, memory_mb,
            extra={
                "process": process_name,
                "memory_mb": memory_mb,
                "event": "memory_metric"
            }
        )

    def log_concurrent_downloads(self, active_count: int, queued_count: int) -> None:
        """记录并发下载数量."""
        self.logger.info(
            "Concurrent downloads: %d active, %d queued",
            active_count, queued_count,
            extra={
                "active_downloads": active_count,
                "queued_downloads": queued_count,
                "total_downloads": active_count + queued_count,
                "event": "concurrency_metric"
            }
        )

    def log_disk_usage(self, total_gb: float, used_gb: float, free_gb: float) -> None:
        """记录磁盘使用情况."""
        usage_percentage = (used_gb / total_gb) * 100 if total_gb > 0 else 0
        self.logger.info(
            "Disk usage: %.1f GB used of %.1f GB total (%.1f%% full)",
            used_gb, total_gb, usage_percentage,
            extra={
                "total_gb": total_gb,
                "used_gb": used_gb,
                "free_gb": free_gb,
                "usage_percentage": usage_percentage,
                "event": "disk_metric"
            }
        )

    def log_api_request(
        self,
        endpoint: str,
        method: str,
        duration: float,
        status_code: int
    ) -> None:
        """记录API请求性能."""
        self.logger.info(
            "%s %s completed in %.3fs with status %d",
            method, endpoint, duration, status_code,
            extra={
                "endpoint": endpoint,
                "method": method,
                "duration": duration,
                "status_code": status_code,
                "event": "api_metric"
            }
        )

    def log_websocket_connection(self, connection_count: int, action: str) -> None:
        """记录WebSocket连接数."""
        self.logger.info(
            "WebSocket connection %s: %d active connections",
            action, connection_count,
            extra={
                "connection_count": connection_count,
                "action": action,
                "event": "websocket_metric"
            }
        )