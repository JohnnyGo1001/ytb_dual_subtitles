# API 使用示例

## 统一响应格式

所有API接口都返回统一的JSON响应格式：

```json
{
  "success": true,          // boolean: 操作是否成功
  "data": {...},           // any: 实际返回的数据（成功时）
  "error_code": null,      // string|null: 错误码（失败时）
  "error_msg": null        // string|null: 错误信息（失败时）
}
```

## 成功响应示例

### 1. 创建下载任务

**请求**:
```bash
curl -X POST "http://localhost:8000/api/downloads" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "status": "pending",
    "progress": 0,
    "message": "Task created successfully"
  },
  "error_code": null,
  "error_msg": null
}
```

### 2. 获取下载任务状态

**请求**:
```bash
curl "http://localhost:8000/api/downloads/task_123456"
```

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "task_123456",
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "status": "downloading",
    "progress": 45,
    "message": "Downloading video... 45% complete"
  },
  "error_code": null,
  "error_msg": null
}
```

### 3. 获取视频列表

**请求**:
```bash
curl "http://localhost:8000/api/videos?page=1&per_page=10"
```

**响应**:
```json
{
  "success": true,
  "data": {
    "videos": [
      {
        "id": 1,
        "youtube_id": "dQw4w9WgXcQ",
        "title": "Never Gonna Give You Up",
        "duration": 213,
        "file_path": "/path/to/video.mp4",
        "status": "completed",
        "created_at": "2024-02-01T10:00:00Z",
        "updated_at": "2024-02-01T10:05:00Z",
        "thumbnail_url": "/api/videos/1/thumbnail/medium",
        "has_subtitles": true
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 1,
      "total_pages": 1
    }
  },
  "error_code": null,
  "error_msg": null
}
```

## 错误响应示例

### 1. 无效的YouTube URL

**请求**:
```bash
curl -X POST "http://localhost:8000/api/downloads" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://invalid-url.com"}'
```

**响应**:
```json
{
  "success": false,
  "data": null,
  "error_code": "INVALID_URL",
  "error_msg": "Invalid YouTube URL format"
}
```

### 2. 任务未找到

**请求**:
```bash
curl "http://localhost:8000/api/downloads/nonexistent_task"
```

**响应**:
```json
{
  "success": false,
  "data": null,
  "error_code": "TASK_NOT_FOUND",
  "error_msg": "Task not found"
}
```

### 3. 验证错误

**请求**:
```bash
curl -X POST "http://localhost:8000/api/downloads" \
  -H "Content-Type: application/json" \
  -d '{"invalid_field": "value"}'
```

**响应**:
```json
{
  "success": false,
  "data": null,
  "error_code": "VALIDATION_ERROR",
  "error_msg": "Validation error: field required"
}
```

## 错误码说明

| 错误码 | 说明 | HTTP状态码 |
|--------|------|------------|
| `INVALID_URL` | 无效的YouTube URL | 200 |
| `DOWNLOAD_FAILED` | 下载失败 | 200 |
| `TASK_NOT_FOUND` | 任务未找到 | 200 |
| `TASK_ALREADY_EXISTS` | 任务已存在 | 200 |
| `FILE_NOT_FOUND` | 文件未找到 | 200 |
| `FILE_ACCESS_DENIED` | 文件访问被拒绝 | 200 |
| `INSUFFICIENT_SPACE` | 磁盘空间不足 | 200 |
| `SUBTITLE_NOT_FOUND` | 字幕未找到 | 200 |
| `TRANSLATION_FAILED` | 翻译失败 | 200 |
| `SUBTITLE_GENERATION_FAILED` | 字幕生成失败 | 200 |
| `VALIDATION_ERROR` | 请求参数验证错误 | 422 |
| `NOT_FOUND` | 资源未找到 | 404 |
| `PERMISSION_DENIED` | 权限被拒绝 | 403 |
| `INTERNAL_ERROR` | 内部服务器错误 | 500 |

## 前端处理示例

### JavaScript/TypeScript

```typescript
interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error_code?: string;
  error_msg?: string;
}

async function createDownloadTask(url: string): Promise<any> {
  try {
    const response = await fetch('/api/downloads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    const result: ApiResponse = await response.json();

    if (result.success) {
      console.log('Task created:', result.data);
      return result.data;
    } else {
      console.error('Error:', result.error_code, result.error_msg);
      throw new Error(result.error_msg);
    }
  } catch (error) {
    console.error('Network error:', error);
    throw error;
  }
}
```

### React Hook 示例

```typescript
import { useState, useCallback } from 'react';

interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (...args: any[]) => Promise<T>;
}

function useApi<T>(apiCall: (...args: any[]) => Promise<ApiResponse<T>>): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (...args: any[]): Promise<T> => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiCall(...args);

      if (response.success) {
        setData(response.data);
        return response.data;
      } else {
        const errorMsg = `${response.error_code}: ${response.error_msg}`;
        setError(errorMsg);
        throw new Error(errorMsg);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiCall]);

  return { data, loading, error, execute };
}
```

## 健康检查

**请求**:
```bash
curl "http://localhost:8000/health"
```

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "0.1.0"
  },
  "error_code": null,
  "error_msg": null
}
```

这种统一的响应格式使得前端处理更加一致和可靠，减少了错误处理的复杂性。