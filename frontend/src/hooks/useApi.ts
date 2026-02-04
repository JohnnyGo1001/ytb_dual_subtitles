import { useState, useCallback } from 'react';
import type { ApiResponse } from '@/types/common';

interface UseApiState<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
}

interface UseApiReturn<T> extends UseApiState<T> {
  execute: (apiCall: () => Promise<ApiResponse<T>>) => Promise<T | null>;
  clearError: () => void;
  reset: () => void;
}

/**
 * 自定义Hook用于处理API请求状态
 */
export function useApi<T = unknown>(): UseApiReturn<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const execute = useCallback(async (apiCall: () => Promise<ApiResponse<T>>) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await apiCall();

      if (response.success) {
        setState({
          data: response.data || null,
          isLoading: false,
          error: null,
        });
        return response.data || null;
      } else {
        const errorMessage = response.error_msg || `Error ${response.error_code || 'UNKNOWN'}`;
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: errorMessage,
        }));
        return null;
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Network error occurred';
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