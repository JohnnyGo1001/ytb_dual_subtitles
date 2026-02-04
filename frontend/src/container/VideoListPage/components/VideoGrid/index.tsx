import React from 'react';
import Loading from '@/components/Loading';
import VideoCard from '../VideoCard';
import type { Video } from '@/types/video';
import styles from './index.module.css';

interface VideoGridProps {
  videos: Video[];
  loading?: boolean;
  onPlay: (video: Video) => void;
  onDelete: (video: Video) => void;
  onExportSubtitle: (video: Video) => void;
}

const VideoGrid: React.FC<VideoGridProps> = ({
  videos,
  loading = false,
  onPlay,
  onDelete,
  onExportSubtitle,
}) => {
  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <Loading size="large" text="加载视频列表中..." />
      </div>
    );
  }

  if (videos.length === 0) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>📺</div>
        <h3 className={styles.emptyTitle}>暂无视频</h3>
        <p className={styles.emptyDescription}>
          还没有下载任何视频，去下载页面下载您的第一个视频吧！
        </p>
      </div>
    );
  }

  return (
    <div className={styles.videoGrid}>
      {videos.map((video) => (
        <VideoCard
          key={video.id}
          video={video}
          onPlay={onPlay}
          onDelete={onDelete}
          onExportSubtitle={onExportSubtitle}
        />
      ))}
    </div>
  );
};

export default VideoGrid;