import { useCallback } from 'react';
import { useApi } from '@/hooks/useApi';
import { useToast } from '@/contexts/ToastContext';
import type { ApiResponse } from '@/types/common';

interface UseApiWithToastOptions {
  successMessage?: string;
  errorPrefix?: string;
  showSuccessToast?: boolean;
  showErrorToast?: boolean;
}

interface UseApiWithToastReturn<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  execute: (apiCall: () => Promise<ApiResponse<T>>, options?: UseApiWithToastOptions) => Promise<T | null>;
  clearError: () => void;
  reset: () => void;
}

/**
 * 自定义Hook，结合useApi和Toast功能
 * 自动处理API请求的成功和错误消息显示
 */
export function useApiWithToast<T = unknown>(
  defaultOptions: UseApiWithToastOptions = {}
): UseApiWithToastReturn<T> {
  const { showToast } = useToast();
  const apiHook = useApi<T>();

  const execute = useCallback(async (
    apiCall: () => Promise<ApiResponse<T>>,
    options: UseApiWithToastOptions = {}
  ): Promise<T | null> => {
    const mergedOptions = { ...defaultOptions, ...options };
    const {
      successMessage,
      errorPrefix = '操作失败',
      showSuccessToast = false,
      showErrorToast = true
    } = mergedOptions;

    const result = await apiHook.execute(apiCall);

    if (result !== null) {
      // 成功
      if (showSuccessToast && successMessage) {
        showToast(successMessage, 'success');
      }
    } else {
      // 失败
      if (showErrorToast && apiHook.error) {
        const errorMessage = `${errorPrefix}: ${apiHook.error}`;
        showToast(errorMessage, 'error');
      }
    }

    return result;
  }, [apiHook, showToast, defaultOptions]);

  return {
    ...apiHook,
    execute,
  };
}

/**
 * 专门用于下载操作的Hook
 */
export function useDownloadApi<T = unknown>() {
  return useApiWithToast<T>({
    errorPrefix: '下载操作失败',
    showErrorToast: true,
  });
}

/**
 * 专门用于删除操作的Hook
 */
export function useDeleteApi<T = unknown>() {
  return useApiWithToast<T>({
    successMessage: '删除成功',
    errorPrefix: '删除失败',
    showSuccessToast: true,
    showErrorToast: true,
  });
}

/**
 * 专门用于视频操作的Hook
 */
export function useVideoApi<T = unknown>() {
  return useApiWithToast<T>({
    errorPrefix: '视频操作失败',
    showErrorToast: true,
  });
}