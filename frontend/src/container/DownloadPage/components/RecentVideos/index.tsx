import React from 'react';
import { Link } from 'react-router-dom';
import Loading from '@/components/Loading';
import { ProgressCard } from '../ProgressCard';
import type { DownloadTask } from '@/types/api';
import styles from './index.module.css';

export interface RecentVideosProps {
  tasks: DownloadTask[];
  loading?: boolean;
  maxItems?: number;
  showViewAll?: boolean;
  onTaskClick: (task: DownloadTask) => void;
  onCancelTask: (taskId: string) => void;
}

export const RecentVideos: React.FC<RecentVideosProps> = ({
  tasks,
  loading = false,
  maxItems = 5,
  showViewAll = true,
  onTaskClick,
  onCancelTask,
}) => {
  // Sort tasks by creation date (newest first) and limit items
  const sortedTasks = [...tasks]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, maxItems);

  const hasMoreTasks = tasks.length > maxItems;

  if (loading) {
    return (
      <div className={styles.container}>
        <h3 className={styles.title}>最近下载</h3>
        <div className={styles.loadingContainer}>
          <Loading text="加载中..." />
        </div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className={styles.container}>
        <h3 className={styles.title}>最近下载</h3>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>📺</div>
          <h4 className={styles.emptyTitle}>暂无最近下载</h4>
          <p className={styles.emptyDescription}>
            开始下载您的第一个视频来查看下载历史
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>最近下载</h3>
        {hasMoreTasks && showViewAll && (
          <Link to="/downloads" className={styles.viewAllLink}>
            查看全部
          </Link>
        )}
      </div>

      <div className={styles.taskList}>
        {sortedTasks.map((task) => (
          <div
            key={task.id}
            className={styles.taskItem}
            data-testid={`task-item-${task.id}`}
            onClick={() => onTaskClick(task)}
          >
            <ProgressCard
              task={task}
              onCancel={onCancelTask}
            />
          </div>
        ))}
      </div>
    </div>
  );
};