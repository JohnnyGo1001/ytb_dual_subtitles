/**
 * API集成测试
 * 测试前端如何处理新的统一API响应格式
 */

import { apiService } from '@/services/api';
import { formatErrorForDisplay, getErrorMessage } from '@/utils/apiErrorHandler';
import type { ApiResponse } from '@/types/common';

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('API Integration Tests', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('Success Responses', () => {
    it('should handle download task creation success', async () => {
      const successResponse = {
        success: true,
        data: {
          task_id: 'task_123456',
          url: 'https://www.youtube.com/watch?v=test',
          status: 'pending',
          progress: 0,
          message: 'Task created successfully'
        },
        error_code: null,
        error_msg: null
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => successResponse,
      } as Response);

      const result = await apiService.createDownload({
        url: 'https://www.youtube.com/watch?v=test'
      });

      expect(result).toEqual(successResponse);
      expect(result.success).toBe(true);
      expect(result.data?.task_id).toBe('task_123456');
    });

    it('should handle video list success', async () => {
      const successResponse = {
        success: true,
        data: {
          videos: [
            {
              id: 1,
              youtube_id: 'test123',
              title: 'Test Video',
              status: 'completed',
              created_at: '2024-02-01T10:00:00Z',
              thumbnail_url: '/api/videos/1/thumbnail/medium',
              has_subtitles: true
            }
          ],
          pagination: {
            page: 1,
            per_page: 10,
            total: 1,
            total_pages: 1
          }
        },
        error_code: null,
        error_msg: null
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => successResponse,
      } as Response);

      const result = await apiService.getVideos(1, 10);

      expect(result).toEqual(successResponse);
      expect(result.success).toBe(true);
      expect(result.data?.videos).toHaveLength(1);
      expect(result.data?.pagination.total).toBe(1);
    });
  });

  describe('Error Responses', () => {
    it('should handle invalid URL error', async () => {
      const errorResponse = {
        success: false,
        data: null,
        error_code: 'INVALID_URL',
        error_msg: 'Invalid YouTube URL format'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true, // 注意：业务错误仍然返回HTTP 200
        json: async () => errorResponse,
      } as Response);

      const result = await apiService.createDownload({
        url: 'invalid-url'
      });

      expect(result).toEqual(errorResponse);
      expect(result.success).toBe(false);
      expect(result.error_code).toBe('INVALID_URL');
    });

    it('should handle task not found error', async () => {
      const errorResponse = {
        success: false,
        data: null,
        error_code: 'TASK_NOT_FOUND',
        error_msg: 'Task not found'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => errorResponse,
      } as Response);

      const result = await apiService.getDownloadStatus('nonexistent-task');

      expect(result).toEqual(errorResponse);
      expect(result.success).toBe(false);
      expect(result.error_code).toBe('TASK_NOT_FOUND');
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network failure'));

      const result = await apiService.createDownload({
        url: 'https://www.youtube.com/watch?v=test'
      });

      expect(result.success).toBe(false);
      expect(result.error_code).toBe('NETWORK_ERROR');
      expect(result.error_msg).toContain('Network failure');
    });

    it('should handle HTTP errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({}),
      } as Response);

      const result = await apiService.createDownload({
        url: 'https://www.youtube.com/watch?v=test'
      });

      expect(result.success).toBe(false);
      expect(result.error_code).toBe('HTTP_ERROR');
      expect(result.error_msg).toContain('HTTP 500');
    });
  });

  describe('Error Message Formatting', () => {
    it('should format error messages correctly', () => {
      const errorResponse: ApiResponse<any> = {
        success: false,
        error_code: 'INVALID_URL',
        error_msg: 'Invalid YouTube URL format'
      };

      const formatted = formatErrorForDisplay(errorResponse);
      expect(formatted).toBe('💡 Invalid YouTube URL format');
    });

    it('should handle unknown error codes', () => {
      const errorResponse: ApiResponse<any> = {
        success: false,
        error_code: 'UNKNOWN_ERROR',
        error_msg: 'Something went wrong'
      };

      const formatted = formatErrorForDisplay(errorResponse);
      expect(formatted).toBe('🔄 Something went wrong');
    });

    it('should provide default messages for missing error_msg', () => {
      const message = getErrorMessage('INVALID_URL');
      expect(message).toBe('请输入有效的YouTube URL');

      const unknownMessage = getErrorMessage('NONEXISTENT_ERROR');
      expect(unknownMessage).toBe('NONEXISTENT_ERROR');
    });
  });

  describe('Backward Compatibility', () => {
    it('should handle old API format', async () => {
      // 模拟旧格式响应
      const oldFormatResponse = {
        data: { id: 1, name: 'test' },
        success: true,
        message: 'Operation successful'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => oldFormatResponse,
      } as Response);

      const result = await apiService.createDownload({
        url: 'https://www.youtube.com/watch?v=test'
      });

      // 应该被转换为新格式
      expect(result.success).toBe(true);
      expect(result.data).toEqual(oldFormatResponse);
    });
  });

  describe('Real API Integration', () => {
    // 这些测试需要真实的API服务器运行
    // 可以在集成测试环境中启用

    it.skip('should create download task with real API', async () => {
      const result = await apiService.createDownload({
        url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
      });

      if (result.success) {
        expect(result.data).toBeDefined();
        expect(result.data?.task_id).toBeTruthy();
      } else {
        console.log('API Error:', result.error_code, result.error_msg);
      }
    });

    it.skip('should get video list with real API', async () => {
      const result = await apiService.getVideos();

      if (result.success) {
        expect(result.data).toBeDefined();
        expect(Array.isArray(result.data?.videos)).toBe(true);
        expect(result.data?.pagination).toBeDefined();
      } else {
        console.log('API Error:', result.error_code, result.error_msg);
      }
    });
  });
});

describe('Error Handler Utils', () => {
  it('should categorize error severities correctly', () => {
    const { getErrorSeverity } = require('@/utils/apiErrorHandler');

    expect(getErrorSeverity('VALIDATION_ERROR')).toBe('low');
    expect(getErrorSeverity('NETWORK_ERROR')).toBe('medium');
    expect(getErrorSeverity('INTERNAL_ERROR')).toBe('high');
    expect(getErrorSeverity('UNKNOWN_ERROR')).toBe('medium');
  });

  it('should detect error types correctly', () => {
    const { isNetworkError, isUserInputError, isServerError } = require('@/utils/apiErrorHandler');

    expect(isNetworkError('NETWORK_ERROR')).toBe(true);
    expect(isUserInputError('VALIDATION_ERROR')).toBe(true);
    expect(isServerError('INTERNAL_ERROR')).toBe(true);

    expect(isNetworkError('INVALID_URL')).toBe(false);
    expect(isUserInputError('DOWNLOAD_FAILED')).toBe(false);
    expect(isServerError('TASK_NOT_FOUND')).toBe(false);
  });
});

// 性能测试
describe('Performance Tests', () => {
  it('should handle multiple concurrent requests', async () => {
    const responses = Array.from({ length: 10 }, (_, i) => ({
      success: true,
      data: { id: i, task_id: `task_${i}` },
    }));

    mockFetch.mockImplementation(async () => ({
      ok: true,
      json: async () => responses[Math.floor(Math.random() * responses.length)],
    }) as Response);

    const promises = Array.from({ length: 10 }, () =>
      apiService.createDownload({ url: 'https://www.youtube.com/watch?v=test' })
    );

    const results = await Promise.all(promises);

    results.forEach(result => {
      expect(result.success).toBe(true);
    });
  });

  it('should handle request timeouts gracefully', async () => {
    mockFetch.mockImplementation(
      () => new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), 100)
      )
    );

    const result = await apiService.createDownload({
      url: 'https://www.youtube.com/watch?v=test'
    });

    expect(result.success).toBe(false);
    expect(result.error_code).toBe('NETWORK_ERROR');
    expect(result.error_msg).toContain('Request timeout');
  });
});