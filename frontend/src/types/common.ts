// 通用类型定义

export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at: string;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error_code?: string;
  error_msg?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

export type Theme = 'light' | 'dark';

export interface ComponentProps {
  className?: string;
  children?: React.ReactNode;
}