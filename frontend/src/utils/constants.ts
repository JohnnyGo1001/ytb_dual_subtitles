// API配置常量
export const API_BASE_URL = '/api';
export const WS_BASE_URL = '/ws';

// 下载配置
export const DOWNLOAD_CONFIG = {
  MAX_CONCURRENT_DOWNLOADS: 3,
  RETRY_ATTEMPTS: 3,
  TIMEOUT_MS: 300000, // 5分钟
} as const;

// 视频配置
export const VIDEO_CONFIG = {
  SUPPORTED_FORMATS: ['mp4', 'webm'] as const,
  SUPPORTED_QUALITIES: ['best', 'worst', 'bestvideo', 'bestaudio'] as const,
  MAX_TITLE_LENGTH: 100,
  THUMBNAIL_SIZES: {
    small: '120x90',
    medium: '320x180',
    large: '480x360',
  },
} as const;

// UI配置
export const UI_CONFIG = {
  TOAST_DURATION: 5000,
  DEBOUNCE_DELAY: 300,
  PAGINATION_SIZE: 12,
  MOBILE_BREAKPOINT: 768,
  TABLET_BREAKPOINT: 1024,
} as const;

// WebSocket事件类型
export const WS_EVENTS = {
  PROGRESS: 'progress',
  STATUS: 'status',
  ERROR: 'error',
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
} as const;

// 路由路径
export const ROUTES = {
  HOME: '/',
  VIDEOS: '/videos',
  PLAYER: '/player',
  NOT_FOUND: '*',
} as const;