import type {
  ApiResponse,
  PaginatedResponse
} from '@/types/common';
import type {
  DownloadRequest,
  DownloadTask
} from '@/types/api';
import type { Video } from '@/types/video';

export class ApiService {
  private baseURL = '/api';

  /**
   * 通用请求方法
   */
  private async request<T = unknown>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;

    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      const data = await response.json();

      // 如果HTTP状态码不是200系列，但返回了JSON，说明是业务错误
      if (!response.ok) {
        // 如果返回的是统一格式的错误响应，直接返回
        if (data && 'success' in data) {
          return data;
        }

        // 否则构造错误响应
        return {
          success: false,
          error_code: 'HTTP_ERROR',
          error_msg: `HTTP ${response.status}: ${response.statusText}`
        };
      }

      // 确保返回的数据有统一的格式
      if (data && 'success' in data) {
        return data;
      }

      // 如果是旧格式，转换为新格式
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

  /**
   * 创建下载任务
   */
  async createDownload(request: DownloadRequest): Promise<ApiResponse<DownloadTask>> {
    return this.request<DownloadTask>('/downloads', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * 获取下载任务列表
   */
  async getDownloads(): Promise<ApiResponse<DownloadTask[]>> {
    return this.request<DownloadTask[]>('/list/downloads');
  }

  /**
   * 获取下载任务状态
   */
  async getDownloadStatus(taskId: string): Promise<ApiResponse<DownloadTask>> {
    return this.request<DownloadTask>(`/downloads/${taskId}`);
  }

  /**
   * 取消下载任务
   */
  async cancelDownload(taskId: string): Promise<ApiResponse<string>> {
    return this.request<string>(`/downloads/${taskId}`, {
      method: 'DELETE',
    });
  }

  /**
   * 获取所有任务状态（用于轮询）
   */
  async getAllTasksStatus(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/status');
  }

  /**
   * 获取特定任务状态（用于轮询）
   */
  async getTaskStatusPolling(taskId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/status/${taskId}`);
  }

  /**
   * 获取视频列表
   */
  async getVideos(
    page = 1,
    per_page = 10,
    search?: string,
    sort_by = 'created_at',
    sort_order: 'asc' | 'desc' = 'desc'
  ): Promise<ApiResponse<{videos: Video[], pagination: {page: number, per_page: number, total: number, total_pages: number}}>> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: per_page.toString(),
      sort_by,
      sort_order,
    });

    if (search) {
      params.set('search', search);
    }

    return this.request(`/videos?${params}`);
  }

  /**
   * 获取视频详情
   */
  async getVideo(videoId: string): Promise<ApiResponse<Video>> {
    return this.request<Video>(`/videos/${videoId}`);
  }

  /**
   * 删除视频
   */
  async deleteVideo(videoId: string): Promise<ApiResponse<{message: string, video_id: string}>> {
    return this.request<{message: string, video_id: string}>(`/videos/${videoId}`, {
      method: 'DELETE',
    });
  }

  /**
   * 获取字幕数据
   */
  async getSubtitles(videoId: string): Promise<ApiResponse<import('@/types/video').SubtitleData>> {
    return this.request<import('@/types/video').SubtitleData>(`/subtitles/${videoId}`);
  }

  /**
   * 导出SRT字幕文件
   */
  async exportSubtitles(
    videoId: string,
    format: 'srt' | 'vtt' = 'srt',
    language: 'en' | 'zh' | 'both' = 'both'
  ): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/subtitles/${videoId}/export?format=${format}&lang=${language}`);

    if (!response.ok) {
      throw new Error(`导出字幕失败: ${response.statusText}`);
    }

    return response.blob();
  }

  /**
   * 获取所有分类
   */
  async getCategories(): Promise<ApiResponse<{categories: Array<{id: number, name: string, description?: string, color?: string, icon?: string, video_count: number}>, total: number}>> {
    return this.request('/categories');
  }

  /**
   * 创建新分类
   */
  async createCategory(data: {name: string, description?: string, color?: string, icon?: string}): Promise<ApiResponse<any>> {
    return this.request('/categories', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * 更新分类
   */
  async updateCategory(categoryId: number, data: {name?: string, description?: string, color?: string, icon?: string}): Promise<ApiResponse<any>> {
    return this.request(`/categories/${categoryId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  /**
   * 删除分类
   */
  async deleteCategory(categoryId: number): Promise<ApiResponse<any>> {
    return this.request(`/categories/${categoryId}`, {
      method: 'DELETE',
    });
  }

  /**
   * 更新视频分类
   */
  async updateVideoCategory(videoId: string, category: string): Promise<ApiResponse<any>> {
    return this.request(`/videos/${videoId}/category?category=${encodeURIComponent(category)}`, {
      method: 'PATCH',
    });
  }
}

// 默认导出单例实例
export const apiService = new ApiService();