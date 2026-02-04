import type { ApiResponse } from '@/types/common';

/**
 * API错误码映射
 */
export const ERROR_MESSAGES = {
  // 通用错误
  INTERNAL_ERROR: '服务器内部错误，请稍后重试',
  VALIDATION_ERROR: '请求参数有误',
  NOT_FOUND: '请求的资源未找到',
  PERMISSION_DENIED: '权限不足',

  // 下载相关错误
  INVALID_URL: '请输入有效的YouTube URL',
  DOWNLOAD_FAILED: '下载失败，请重试',
  TASK_NOT_FOUND: '下载任务未找到',
  TASK_ALREADY_EXISTS: '下载任务已存在',

  // 文件相关错误
  FILE_NOT_FOUND: '文件未找到',
  FILE_ACCESS_DENIED: '文件访问被拒绝',
  INSUFFICIENT_SPACE: '磁盘空间不足',

  // 字幕相关错误
  SUBTITLE_NOT_FOUND: '字幕文件未找到',
  TRANSLATION_FAILED: '翻译失败',
  SUBTITLE_GENERATION_FAILED: '字幕生成失败',

  // 网络错误
  NETWORK_ERROR: '网络连接错误，请检查网络设置',
  HTTP_ERROR: 'HTTP请求错误',

  // 默认错误
  UNKNOWN: '未知错误'
} as const;

/**
 * 获取友好的错误消息
 */
export function getErrorMessage(errorCode?: string): string {
  if (!errorCode) {
    return ERROR_MESSAGES.UNKNOWN;
  }

  return ERROR_MESSAGES[errorCode as keyof typeof ERROR_MESSAGES] || errorCode;
}

/**
 * 处理API响应错误
 */
export function handleApiError<T>(response: ApiResponse<T>): {
  hasError: boolean;
  errorMessage: string;
  errorCode?: string;
} {
  if (response.success) {
    return {
      hasError: false,
      errorMessage: '',
    };
  }

  const errorMessage = response.error_msg || getErrorMessage(response.error_code);

  return {
    hasError: true,
    errorMessage,
    errorCode: response.error_code,
  };
}

/**
 * 创建统一的API错误处理函数
 */
export function createApiErrorHandler(
  onError?: (error: { message: string; code?: string }) => void
) {
  return function<T>(response: ApiResponse<T>): T | null {
    const { hasError, errorMessage, errorCode } = handleApiError(response);

    if (hasError) {
      onError?.({ message: errorMessage, code: errorCode });
      return null;
    }

    return response.data || null;
  };
}

/**
 * 检查是否为网络错误
 */
export function isNetworkError(errorCode?: string): boolean {
  return errorCode === 'NETWORK_ERROR' || errorCode === 'HTTP_ERROR';
}

/**
 * 检查是否为用户输入错误
 */
export function isUserInputError(errorCode?: string): boolean {
  return errorCode === 'VALIDATION_ERROR' || errorCode === 'INVALID_URL';
}

/**
 * 检查是否为服务器错误
 */
export function isServerError(errorCode?: string): boolean {
  return errorCode === 'INTERNAL_ERROR' || errorCode === 'DOWNLOAD_FAILED';
}

/**
 * 获取错误的严重程度
 */
export function getErrorSeverity(errorCode?: string): 'low' | 'medium' | 'high' {
  if (isUserInputError(errorCode)) {
    return 'low';
  }

  if (isNetworkError(errorCode)) {
    return 'medium';
  }

  if (isServerError(errorCode)) {
    return 'high';
  }

  return 'medium';
}

/**
 * 格式化错误消息供显示使用
 */
export function formatErrorForDisplay(response: ApiResponse<any>): string {
  if (response.success) {
    return '';
  }

  const { errorMessage, errorCode } = handleApiError(response);
  const severity = getErrorSeverity(errorCode);

  // 根据错误严重程度添加不同的前缀
  switch (severity) {
    case 'high':
      return `⚠️ ${errorMessage}`;
    case 'medium':
      return `🔄 ${errorMessage}`;
    case 'low':
      return `💡 ${errorMessage}`;
    default:
      return errorMessage;
  }
}