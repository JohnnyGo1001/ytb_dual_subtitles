"""统一API响应模型.

定义所有API接口的统一响应格式。
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# 泛型类型变量，用于指定data字段的具体类型
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应模型.

    所有API接口都应返回此格式的响应。
    """

    success: bool = Field(..., description="是否成功")
    data: T | None = Field(None, description="实际返回的数据")
    error_code: str | None = Field(None, description="错误码")
    error_msg: str | None = Field(None, description="错误信息")

    @classmethod
    def success_response(cls, data: T | None = None) -> ApiResponse[T]:
        """创建成功响应.

        Args:
            data: 返回的数据

        Returns:
            成功响应对象
        """
        return cls(success=True, data=data)

    @classmethod
    def error_response(
        cls,
        error_code: str,
        error_msg: str,
        data: T | None = None
    ) -> ApiResponse[T]:
        """创建错误响应.

        Args:
            error_code: 错误码
            error_msg: 错误信息
            data: 可选的附加数据

        Returns:
            错误响应对象
        """
        return cls(
            success=False,
            data=data,
            error_code=error_code,
            error_msg=error_msg
        )


# 常用的响应类型别名
class StringResponse(ApiResponse[str]):
    """字符串响应类型."""
    pass


class DictResponse(ApiResponse[dict[str, Any]]):
    """字典响应类型."""
    pass


class ListResponse(ApiResponse[list[Any]]):
    """列表响应类型."""
    pass


class BoolResponse(ApiResponse[bool]):
    """布尔响应类型."""
    pass


# 常用错误码定义
class ErrorCodes:
    """API错误码常量."""

    # 通用错误码
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    # 下载相关错误码
    INVALID_URL = "INVALID_URL"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_ALREADY_EXISTS = "TASK_ALREADY_EXISTS"

    # 文件相关错误码
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_ACCESS_DENIED = "FILE_ACCESS_DENIED"
    INSUFFICIENT_SPACE = "INSUFFICIENT_SPACE"

    # 字幕相关错误码
    SUBTITLE_NOT_FOUND = "SUBTITLE_NOT_FOUND"
    TRANSLATION_FAILED = "TRANSLATION_FAILED"
    SUBTITLE_GENERATION_FAILED = "SUBTITLE_GENERATION_FAILED"