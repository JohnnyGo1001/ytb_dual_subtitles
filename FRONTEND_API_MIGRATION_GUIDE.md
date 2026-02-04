# 前端API适配指南

## 概述

本指南说明如何将前端代码适配新的统一API响应格式。新格式提供了一致的错误处理和更好的类型安全性。

## 新的API响应格式

### 统一响应结构

```typescript
interface ApiResponse<T> {
  success: boolean;          // 操作是否成功
  data?: T;                 // 实际数据（成功时）
  error_code?: string;      // 错误码（失败时）
  error_msg?: string;       // 错误信息（失败时）
}
```

### 旧格式 vs 新格式

**旧格式**:
```typescript
// 成功响应
{
  data: {...},
  success: true,
  message?: string
}

// 错误处理通过HTTP状态码和异常
```

**新格式**:
```typescript
// 成功响应
{
  success: true,
  data: {...},
  error_code: null,
  error_msg: null
}

// 错误响应
{
  success: false,
  data: null,
  error_code: "INVALID_URL",
  error_msg: "Invalid YouTube URL format"
}
```

## 迁移步骤

### 1. 更新类型定义

```typescript
// types/common.ts - 更新ApiResponse接口
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error_code?: string;
  error_msg?: string;
}
```

### 2. 更新API服务

```typescript
// services/api.ts
private async request<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    const data = await response.json();

    // 处理HTTP错误
    if (!response.ok) {
      if (data && 'success' in data) {
        return data; // 返回业务错误
      }
      return {
        success: false,
        error_code: 'HTTP_ERROR',
        error_msg: `HTTP ${response.status}: ${response.statusText}`
      };
    }

    // 确保返回统一格式
    if (data && 'success' in data) {
      return data;
    }

    // 兼容旧格式
    return {
      success: true,
      data: data
    };

  } catch (error) {
    return {
      success: false,
      error_code: 'NETWORK_ERROR',
      error_msg: error instanceof Error ? error.message : 'Network request failed'
    };
  }
}
```

### 3. 更新Hooks

#### 新的useApi实现

```typescript
// hooks/useApi.ts
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
```

### 4. 更新组件

#### 下载表单组件示例

```typescript
// 旧代码
const handleSubmit = async () => {
  try {
    const response = await apiService.createDownload(request);
    if (response.success && response.data) {
      onDownloadStart(response.data);
    } else {
      throw new Error('Failed to create download');
    }
  } catch (err) {
    setError('下载创建失败，请重试');
  }
};

// 新代码
const handleSubmit = async () => {
  try {
    const response = await apiService.createDownload(request);
    if (response.success && response.data) {
      onDownloadStart(response.data);
    } else {
      const errorMessage = formatErrorForDisplay(response);
      setError(errorMessage);
    }
  } catch (err) {
    setError('🔄 网络错误，请检查连接后重试');
  }
};
```

### 5. 错误处理工具

创建统一的错误处理工具：

```typescript
// utils/apiErrorHandler.ts
export const ERROR_MESSAGES = {
  INVALID_URL: '请输入有效的YouTube URL',
  DOWNLOAD_FAILED: '下载失败，请重试',
  TASK_NOT_FOUND: '下载任务未找到',
  // ... 更多错误码
} as const;

export function formatErrorForDisplay(response: ApiResponse<any>): string {
  if (response.success) return '';

  const errorMessage = response.error_msg || getErrorMessage(response.error_code);
  const severity = getErrorSeverity(response.error_code);

  switch (severity) {
    case 'high': return `⚠️ ${errorMessage}`;
    case 'medium': return `🔄 ${errorMessage}`;
    case 'low': return `💡 ${errorMessage}`;
    default: return errorMessage;
  }
}
```

## 具体API端点变更

### 下载相关API

```typescript
// 创建下载任务
const response = await apiService.createDownload({url: "..."});
// 响应格式: {success: true, data: {task_id, url, status, progress, message}}

// 获取下载状态
const response = await apiService.getDownloadStatus(taskId);
// 响应格式: {success: true, data: {task_id, url, status, progress, message}}

// 取消下载
const response = await apiService.cancelDownload(taskId);
// 响应格式: {success: true, data: "Task cancelled successfully"}
```

### 视频相关API

```typescript
// 获取视频列表
const response = await apiService.getVideos(page, perPage, search, sortBy, sortOrder);
// 响应格式: {success: true, data: {videos: [...], pagination: {...}}}

// 删除视频
const response = await apiService.deleteVideo(videoId);
// 响应格式: {success: true, data: {message: "Video deleted successfully", video_id: "123"}}
```

## 最佳实践

### 1. 使用类型守卫

```typescript
import { isSuccessResponse, isErrorResponse } from '@/types/apiResponse';

const response = await apiService.createDownload(request);

if (isSuccessResponse(response)) {
  // TypeScript知道response.data存在且类型正确
  onDownloadStart(response.data);
} else if (isErrorResponse(response)) {
  // TypeScript知道response.error_code和error_msg存在
  console.error(`Error ${response.error_code}: ${response.error_msg}`);
}
```

### 2. 统一错误处理

```typescript
// 使用自定义Hook
const { execute, isLoading, error } = useApiWithToast<DownloadTaskData>({
  successMessage: '下载任务创建成功',
  errorPrefix: '下载创建失败',
});

const handleDownload = async () => {
  const result = await execute(() => apiService.createDownload(request));
  if (result) {
    // 处理成功结果
  }
  // 错误会自动显示Toast
};
```

### 3. 批量操作处理

```typescript
const handleBatchDelete = async (videoIds: string[]) => {
  const results = await Promise.allSettled(
    videoIds.map(id => apiService.deleteVideo(id))
  );

  const successes = results
    .filter(result => result.status === 'fulfilled' && result.value.success)
    .length;

  const failures = results.length - successes;

  showToast(
    failures > 0
      ? `删除完成：成功${successes}个，失败${failures}个`
      : `成功删除${successes}个视频`,
    failures > 0 ? 'warning' : 'success'
  );
};
```

## 测试示例

### 单元测试

```typescript
// __tests__/apiService.test.ts
describe('ApiService', () => {
  it('should handle success response correctly', async () => {
    const mockResponse = {
      success: true,
      data: { task_id: '123', url: 'test-url', status: 'pending' }
    };

    fetchMock.mockResponseOnce(JSON.stringify(mockResponse));

    const result = await apiService.createDownload({ url: 'test-url' });

    expect(result).toEqual(mockResponse);
  });

  it('should handle error response correctly', async () => {
    const mockResponse = {
      success: false,
      error_code: 'INVALID_URL',
      error_msg: 'Invalid YouTube URL format'
    };

    fetchMock.mockResponseOnce(JSON.stringify(mockResponse));

    const result = await apiService.createDownload({ url: 'invalid-url' });

    expect(result).toEqual(mockResponse);
  });
});
```

### 集成测试

```typescript
// __tests__/DownloadForm.test.tsx
describe('DownloadForm', () => {
  it('should display error message on API failure', async () => {
    const mockApiService = {
      createDownload: jest.fn().mockResolvedValue({
        success: false,
        error_code: 'INVALID_URL',
        error_msg: 'Invalid YouTube URL format'
      })
    };

    render(<DownloadForm />, { mockApiService });

    const input = screen.getByPlaceholderText(/YouTube/);
    const button = screen.getByText(/开始下载/);

    await user.type(input, 'invalid-url');
    await user.click(button);

    expect(await screen.findByText(/💡.*Invalid YouTube URL format/)).toBeInTheDocument();
  });
});
```

## 常见问题

### Q: 为什么所有响应的HTTP状态码都是200？

A: 新的API设计采用业务状态与HTTP状态分离的方式。HTTP 200表示网络通信成功，业务成功/失败由响应体中的`success`字段表示。这样可以：
- 统一前端的错误处理逻辑
- 避免浏览器自动处理某些HTTP错误状态
- 提供更详细的业务错误信息

### Q: 如何处理网络错误？

A: 网络错误（连接失败、超时等）仍然会触发fetch的异常，在API服务层会被捕获并转换为统一格式：

```typescript
{
  success: false,
  error_code: 'NETWORK_ERROR',
  error_msg: 'Network request failed'
}
```

### Q: 如何向后兼容旧的API？

A: 在API服务的request方法中，我们添加了兼容性处理：

```typescript
// 如果响应已经是新格式，直接返回
if (data && 'success' in data) {
  return data;
}

// 如果是旧格式，转换为新格式
return {
  success: true,
  data: data
};
```

这确保了渐进式迁移的可能性。

## 迁移检查清单

- [ ] 更新`types/common.ts`中的`ApiResponse`接口
- [ ] 更新`services/api.ts`中的请求处理逻辑
- [ ] 更新所有使用API的Hook（`useApi`, `useApiWithToast`等）
- [ ] 更新组件中的错误处理逻辑
- [ ] 添加错误处理工具函数
- [ ] 更新单元测试和集成测试
- [ ] 验证所有API端点的响应格式
- [ ] 测试错误场景的用户体验
- [ ] 更新文档和示例代码

## 总结

新的统一API响应格式提供了：

1. **一致性**: 所有API都返回相同的响应结构
2. **类型安全**: 更好的TypeScript支持
3. **错误处理**: 统一的错误码和消息系统
4. **用户体验**: 更友好的错误提示
5. **可维护性**: 简化的前端逻辑

通过遵循本指南，您的前端应用将能够充分利用新API格式的优势，同时保持向后兼容性。