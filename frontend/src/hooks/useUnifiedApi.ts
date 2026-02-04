import { useState, useCallback } from 'react';
import type { UnifiedApiResponse } from '@/types/apiResponse';
import { formatErrorForDisplay } from '@/utils/apiErrorHandler';

interface UseUnifiedApiState<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
}

interface UseUnifiedApiReturn<T> extends UseUnifiedApiState<T> {
  execute: (apiCall: () => Promise<UnifiedApiResponse<T>>) => Promise<T | null>;
  clearError: () => void;
  reset: () => void;
}

/**
 * 专门处理统一API响应格式的Hook
 */
export function useUnifiedApi<T = unknown>(): UseUnifiedApiReturn<T> {
  const [state, setState] = useState<UseUnifiedApiState<T>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const execute = useCallback(async (
    apiCall: () => Promise<UnifiedApiResponse<T>>
  ): Promise<T | null> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await apiCall();

      if (response.success && response.data !== undefined) {
        setState({
          data: response.data,
          isLoading: false,
          error: null,
        });
        return response.data;
      } else {
        const errorMessage = formatErrorForDisplay(response);
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: errorMessage,
        }));
        return null;
      }
    } catch (error) {
      const errorMessage = error instanceof Error
        ? `🔄 网络错误: ${error.message}`
        : '🔄 网络连接失败';

      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      return null;
    }
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const reset = useCallback(() => {
    setState({
      data: null,
      isLoading: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    execute,
    clearError,
    reset,
  };
}

/**
 * 带自动重试功能的API Hook
 */
export function useUnifiedApiWithRetry<T = unknown>(
  maxRetries = 3,
  retryDelay = 1000
): UseUnifiedApiReturn<T> & { retry: () => Promise<void> } {
  const api = useUnifiedApi<T>();
  const [lastApiCall, setLastApiCall] = useState<(() => Promise<UnifiedApiResponse<T>>) | null>(null);

  const executeWithRetry = useCallback(async (
    apiCall: () => Promise<UnifiedApiResponse<T>>
  ): Promise<T | null> => {
    setLastApiCall(() => apiCall);

    let lastError: any;
    let attempt = 0;

    while (attempt < maxRetries) {
      try {
        const result = await api.execute(apiCall);

        // 如果成功，返回结果
        if (result !== null) {
          return result;
        }

        // 如果是业务逻辑错误（非网络错误），不重试
        if (api.error && !api.error.includes('网络错误') && !api.error.includes('网络连接失败')) {
          return null;
        }

        attempt++;
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, retryDelay * attempt));
        }
      } catch (error) {
        lastError = error;
        attempt++;
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, retryDelay * attempt));
        }
      }
    }

    // 所有重试都失败了
    throw lastError || new Error('所有重试尝试都失败了');
  }, [api, maxRetries, retryDelay]);

  const retry = useCallback(async (): Promise<void> => {
    if (lastApiCall) {
      await executeWithRetry(lastApiCall);
    }
  }, [lastApiCall, executeWithRetry]);

  return {
    ...api,
    execute: executeWithRetry,
    retry,
  };
}