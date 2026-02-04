// 视频相关类型定义

import { BaseEntity } from './common';

export interface Video extends BaseEntity {
  title: string;
  description?: string;
  youtube_id: string;
  duration: number;
  thumbnail_url?: string;
  file_path: string;
  file_size: number;
  download_url: string;
  subtitle_available: boolean;
  view_count?: number;
  upload_date?: string;
  channel_name?: string;
}

export interface SubtitleSegment {
  id: string;
  video_id: string;
  start_time: number;
  end_time: number;
  text_english: string;
  text_chinese?: string;
  sequence: number;
}

export interface SubtitleData {
  video_id: string;
  segments: SubtitleSegment[];
  language_original: string;
  language_translated?: string;
}

export interface PlayerState {
  currentTime: number;
  duration: number;
  isPlaying: boolean;
  volume: number;
  playbackRate: number;
  isFullscreen: boolean;
}