// 统一的API响应类型定义，与后端保持一致

/**
 * 统一API响应接口
 */
export interface UnifiedApiResponse<T = any> {
  success: boolean;
  data?: T;
  error_code?: string;
  error_msg?: string;
}

/**
 * 下载任务响应数据
 */
export interface DownloadTaskData {
  task_id: string;
  url: string;
  status: string;
  progress: number;
  message: string;
}

/**
 * 视频列表响应数据
 */
export interface VideoListData {
  videos: VideoData[];
  pagination: PaginationData;
}

/**
 * 视频数据
 */
export interface VideoData {
  id: number;
  youtube_id: string;
  title: string;
  duration?: number;
  file_path?: string;
  status: string;
  created_at?: string;
  updated_at?: string;
  thumbnail_url: string;
  has_subtitles: boolean;
}

/**
 * 分页数据
 */
export interface PaginationData {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

/**
 * 删除操作响应数据
 */
export interface DeleteResponseData {
  message: string;
  video_id: string;
}

/**
 * 通用错误码常量
 */
export const ErrorCodes = {
  // 通用错误
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  NOT_FOUND: 'NOT_FOUND',
  PERMISSION_DENIED: 'PERMISSION_DENIED',

  // 下载相关错误
  INVALID_URL: 'INVALID_URL',
  DOWNLOAD_FAILED: 'DOWNLOAD_FAILED',
  TASK_NOT_FOUND: 'TASK_NOT_FOUND',
  TASK_ALREADY_EXISTS: 'TASK_ALREADY_EXISTS',

  // 文件相关错误
  FILE_NOT_FOUND: 'FILE_NOT_FOUND',
  FILE_ACCESS_DENIED: 'FILE_ACCESS_DENIED',
  INSUFFICIENT_SPACE: 'INSUFFICIENT_SPACE',

  // 字幕相关错误
  SUBTITLE_NOT_FOUND: 'SUBTITLE_NOT_FOUND',
  TRANSLATION_FAILED: 'TRANSLATION_FAILED',
  SUBTITLE_GENERATION_FAILED: 'SUBTITLE_GENERATION_FAILED',

  // 网络错误
  NETWORK_ERROR: 'NETWORK_ERROR',
  HTTP_ERROR: 'HTTP_ERROR',
} as const;

/**
 * 错误码类型
 */
export type ErrorCodeType = keyof typeof ErrorCodes;

/**
 * API响应状态检查类型守卫
 */
export function isSuccessResponse<T>(
  response: UnifiedApiResponse<T>
): response is UnifiedApiResponse<T> & { success: true; data: T } {
  return response.success === true && response.data !== undefined;
}

/**
 * API错误响应检查类型守卫
 */
export function isErrorResponse<T>(
  response: UnifiedApiResponse<T>
): response is UnifiedApiResponse<T> & { success: false; error_code: string; error_msg: string } {
  return response.success === false;
}