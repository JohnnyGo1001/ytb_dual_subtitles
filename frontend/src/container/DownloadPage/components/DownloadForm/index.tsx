import React, { useState } from 'react';
import Button from '@/components/Button';
import Input from '@/components/Input';
import { apiService } from '@/services/api';
import { formatErrorForDisplay } from '@/utils/apiErrorHandler';
import type { DownloadTask, DownloadRequest } from '@/types/api';
import styles from './index.module.css';

export interface DownloadFormProps {
  onDownloadStart: (task: DownloadTask) => void;
  activeTasks?: DownloadTask[]; // For duplicate URL checking
}

export const DownloadForm: React.FC<DownloadFormProps> = ({ onDownloadStart, activeTasks = [] }) => {
  const [url, setUrl] = useState('');
  const [quality, setQuality] = useState<'best' | '720p' | '1080p'>('best');
  const [format, setFormat] = useState<'mp4' | 'webm'>('mp4');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateYouTubeUrl = (url: string): boolean => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+(&[\w=]*)?$/;
    return youtubeRegex.test(url);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!url.trim()) {
      setError('请输入YouTube URL');
      return;
    }

    if (!validateYouTubeUrl(url.trim())) {
      setError('请输入有效的YouTube URL');
      return;
    }

    // Check for duplicate URL in active tasks
    const normalizedUrl = url.trim();
    const existingTask = activeTasks.find(task =>
      task.url.trim() === normalizedUrl &&
      (task.status === 'pending' || task.status === 'downloading' || task.status === 'processing')
    );

    if (existingTask) {
      setError('该视频已在下载队列中');
      return;
    }

    setIsLoading(true);

    try {
      const request: DownloadRequest = {
        url: url.trim(),
        format,
        quality,
      };

      const response = await apiService.createDownload(request);
      console.log('API response received:', response);
      console.log('Response.success:', response.success);
      console.log('Response.data:', response.data);

      if (response.success && response.data) {
        // Map backend response to frontend DownloadTask format
        const task: DownloadTask = {
          id: response.data.task_id,
          url: response.data.url,
          status: response.data.status as DownloadTask['status'],
          progress: response.data.progress || 0,
          title: response.data.title || '正在获取视频信息...',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        console.log('Mapped task:', task);
        console.log('Calling onDownloadStart with:', task);
        onDownloadStart(task);
        setUrl(''); // Reset form
      } else {
        const errorMessage = formatErrorForDisplay(response);
        setError(errorMessage);
        console.error('Download creation failed:', response);
      }
    } catch (err) {
      setError('🔄 网络错误，请检查连接后重试');
      console.error('Network error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <div className={styles.inputGroup}>
        <Input
          label="YouTube URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="输入YouTube视频链接，如：https://www.youtube.com/watch?v=..."
          error={error || undefined}
          disabled={isLoading}
          required
        />
      </div>

      <div className={styles.optionsGroup}>
        <div className={styles.selectGroup}>
          <label htmlFor="quality-select" className={styles.label}>
            视频质量
          </label>
          <select
            id="quality-select"
            value={quality}
            onChange={(e) => setQuality(e.target.value as any)}
            className={styles.select}
            disabled={isLoading}
          >
            <option key="best" value="best">最佳质量</option>
            <option key="1080p" value="1080p">1080p</option>
            <option key="720p" value="720p">720p</option>
          </select>
        </div>

        <div className={styles.selectGroup}>
          <label htmlFor="format-select" className={styles.label}>
            视频格式
          </label>
          <select
            id="format-select"
            value={format}
            onChange={(e) => setFormat(e.target.value as any)}
            className={styles.select}
            disabled={isLoading}
          >
            <option key="mp4" value="mp4">MP4</option>
            <option key="webm" value="webm">WebM</option>
          </select>
        </div>
      </div>

      <Button
        type="submit"
        loading={isLoading}
        disabled={isLoading || !url.trim()}
        size="large"
        className={styles.submitButton}
        onClick={() => console.log('[DEBUG] Button clicked')}
      >
        {isLoading ? '下载中...' : '开始下载'}
      </Button>
    </form>
  );
};