import React from 'react';
import Button from '@/components/Button';
import type { DownloadTask } from '@/types/api';
import { formatDateTime } from '@/utils/formatters';
import styles from './index.module.css';

export interface ProgressCardProps {
  task: DownloadTask;
  onCancel: (taskId: string) => void;
}

export const ProgressCard: React.FC<ProgressCardProps> = ({ task, onCancel }) => {
  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return '0B';

    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)}${units[unitIndex]}`;
  };

  const formatTime = (seconds?: number): string => {
    if (!seconds) return '';

    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `剩余约 ${hours} 小时 ${minutes % 60} 分钟`;
    } else {
      return `剩余约 ${minutes} 分钟`;
    }
  };

  const getStatusText = (status: DownloadTask['status']): string => {
    switch (status) {
      case 'pending':
        return '等待开始';
      case 'downloading':
        return '下载中';
      case 'completed':
        return '下载完成';
      case 'failed':
        return '下载失败';
      case 'cancelled':
        return '已取消';
      default:
        return status;
    }
  };

  const getStatusColor = (status: DownloadTask['status']): string => {
    switch (status) {
      case 'pending':
        return styles.statusPending;
      case 'downloading':
        return styles.statusDownloading;
      case 'completed':
        return styles.statusCompleted;
      case 'failed':
        return styles.statusFailed;
      case 'cancelled':
        return styles.statusCancelled;
      default:
        return '';
    }
  };

  const canCancel = task.status === 'pending' || task.status === 'downloading';

  return (
    <div className={styles.card}>
      <div className={styles.thumbnail}>
        <img
          src={task.thumbnail || ''}
          alt="Video thumbnail"
          className={styles.thumbnailImage}
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = 'none';
          }}
        />
      </div>

      <div className={styles.content}>
        <div className={styles.header}>
          <h3 className={styles.title}>
            {task.title || 'Loading...'}
          </h3>
          <div className={styles.meta}>
            <span className={styles.format}>
              {task.quality?.toUpperCase()} {task.format?.toUpperCase()}
            </span>
          </div>
        </div>

        <div className={styles.progress}>
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              data-testid="progress-bar"
              style={{ width: `${task.progress}%` }}
            />
          </div>
          <div className={styles.progressInfo}>
            <span className={styles.percentage}>{task.progress}%</span>
            <span className={styles.size}>
              {formatFileSize(task.downloadedSize)} / {formatFileSize(task.fileSize)}
            </span>
          </div>
        </div>

        <div className={styles.status}>
          <span className={`${styles.statusText} ${getStatusColor(task.status)}`}>
            {getStatusText(task.status)}
          </span>

          {task.status === 'failed' && task.error && (
            <span className={styles.errorText}>{task.error}</span>
          )}

          {task.status === 'downloading' && task.estimatedTimeRemaining && (
            <span className={styles.eta}>
              {formatTime(task.estimatedTimeRemaining)}
            </span>
          )}

          {task.createdAt && (
            <span className={styles.timestamp}>
              {formatDateTime(task.createdAt)}
            </span>
          )}
        </div>
      </div>

      {canCancel && (
        <div className={styles.actions}>
          <Button
            variant="secondary"
            size="small"
            onClick={() => onCancel(task.id)}
          >
            取消
          </Button>
        </div>
      )}
    </div>
  );
};