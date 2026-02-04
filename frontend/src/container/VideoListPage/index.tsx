import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { SearchBar, VideoGrid, type SortField, type SortOrder } from './components';
import { useApi } from '@/hooks/useApi';
import { useToast } from '@/contexts/ToastContext';
import { apiService } from '@/services/api';
import { ROUTES, UI_CONFIG } from '@/utils/constants';
import type { Video } from '@/types/video';
import type { PaginatedResponse } from '@/types/common';
import styles from './index.module.css';

function VideoListPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();

  // State management
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // API hooks
  const {
    data: videosResponse,
    isLoading: loading,
    error,
    execute: loadVideos,
  } = useApi<{videos: Video[], pagination: {page: number, per_page: number, total: number, total_pages: number}}>();

  const {
    isLoading: deleting,
    execute: executeDelete,
  } = useApi<{message: string, video_id: string}>();

  // Load videos with current filters
  const fetchVideos = useCallback(async () => {
    const response = await apiService.getVideos(
      1,
      UI_CONFIG.PAGINATION_SIZE,
      searchQuery,
      sortBy,
      sortOrder
    );
    console.log('视频列表API响应:', response); // 调试日志
    return response;
  }, [searchQuery, sortBy, sortOrder]);

  // Load videos on component mount and when filters change
  useEffect(() => {
    loadVideos(fetchVideos);
  }, [loadVideos, fetchVideos]);

  // Handlers
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  const handleSort = useCallback((field: SortField, order: SortOrder) => {
    setSortBy(field);
    setSortOrder(order);
    // The sorting will be handled by the server via fetchVideos dependency
  }, []);

  const handlePlay = useCallback((video: Video) => {
    navigate(`${ROUTES.PLAYER}/${video.id}`);
  }, [navigate]);

  const handleDelete = useCallback(async (video: Video) => {
    if (!window.confirm(`确定要删除视频 "${video.title}" 吗？`)) {
      return;
    }

    const result = await executeDelete(async () => {
      return await apiService.deleteVideo(video.id);
    });

    if (result) {
      showToast('视频删除成功', 'success');
      // Reload videos after deletion
      loadVideos(fetchVideos);
    } else {
      showToast('删除视频失败', 'error');
    }
  }, [executeDelete, showToast, loadVideos, fetchVideos]);

  const handleExportSubtitle = useCallback(async (video: Video) => {
    if (!video.subtitle_available) {
      showToast('该视频没有可用的字幕', 'warning');
      return;
    }

    try {
      const response = await apiService.getSubtitles(video.id);

      if (response.success && response.data) {
        // Create and download SRT file
        const srtContent = generateSRTContent(response.data.segments);
        const blob = new Blob([srtContent], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = `${video.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_')}.srt`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        showToast('字幕导出成功', 'success');
      } else {
        const errorMsg = response.error_msg || '获取字幕数据失败';
        showToast(errorMsg, 'error');
      }
    } catch (err) {
      showToast('导出字幕失败', 'error');
    }
  }, [showToast]);

  // Helper function to generate SRT content
  const generateSRTContent = (segments: any[]): string => {
    return segments
      .map((segment, index) => {
        const startTime = formatSRTTime(segment.start_time);
        const endTime = formatSRTTime(segment.end_time);
        const text = segment.text_chinese || segment.text_english;

        return `${index + 1}\n${startTime} --> ${endTime}\n${text}\n`;
      })
      .join('\n');
  };

  // Helper function to format time for SRT
  const formatSRTTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);

    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms
      .toString()
      .padStart(3, '0')}`;
  };

  const videos = videosResponse?.videos || [];
  const isLoading = loading || deleting;

  // 调试信息
  console.log('videosResponse:', videosResponse);
  console.log('提取的videos数组:', videos);
  console.log('videos数组长度:', videos.length);
  console.log('loading状态:', loading);
  console.log('error状态:', error);

  return (
    <div className={styles.container}>
      {/* Page Header */}
      <div className={styles.header}>
        <h1 className={styles.title}>视频列表</h1>
        <p className={styles.subtitle}>管理您下载的视频和字幕</p>
      </div>

      {/* Search and Sort Controls */}
      <div className={styles.controls}>
        <SearchBar
          onSearch={handleSearch}
          onSort={handleSort}
          searchQuery={searchQuery}
          sortBy={sortBy}
          sortOrder={sortOrder}
        />
      </div>

      {/* Video Grid */}
      <div className={styles.content}>
        <VideoGrid
          videos={videos}
          loading={isLoading}
          onPlay={handlePlay}
          onDelete={handleDelete}
          onExportSubtitle={handleExportSubtitle}
        />
      </div>

      {/* Error Display */}
      {error && (
        <div className={styles.errorContainer}>
          <p className={styles.errorText}>加载视频列表时出现错误，请刷新页面重试。</p>
        </div>
      )}
    </div>
  );
}

export default VideoListPage;