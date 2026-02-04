// API相关类型定义

export interface DownloadRequest {
  url: string;
  format?: 'mp4' | 'webm';
  quality?: 'best' | 'worst' | '720p' | '1080p' | 'bestvideo' | 'bestaudio';
}

export interface DownloadTask {
  id: string;
  url: string;
  title?: string;
  status: 'pending' | 'downloading' | 'processing' | 'completed' | 'failed' | 'cancelled' | 'error';
  progress: number;
  thumbnail?: string;
  format?: 'mp4' | 'webm';
  quality?: 'best' | 'worst' | '720p' | '1080p' | 'bestvideo' | 'bestaudio';
  fileSize?: number;
  downloadedSize?: number;
  speed?: number;
  estimatedTimeRemaining?: number; // ETA in seconds
  error?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ProgressUpdate {
  task_id: string;
  progress: number;
  status: string;
  total_size?: number;
  downloaded_size?: number;
  speed?: number;
  eta?: number;
  error?: string;
}

export interface WebSocketMessage {
  type: 'progress' | 'status' | 'error';
  data: ProgressUpdate | any;
}