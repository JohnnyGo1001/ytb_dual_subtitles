import React from 'react';
import Button from '@/components/Button';
import type { Video } from '@/types/video';
import styles from './index.module.css';

interface VideoCardProps {
  video: Video;
  onPlay: (video: Video) => void;
  onDelete: (video: Video) => void;
  onExportSubtitle: (video: Video) => void;
}

const VideoCard: React.FC<VideoCardProps> = ({
  video,
  onPlay,
  onDelete,
  onExportSubtitle,
}) => {
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const formatFileSize = (bytes: number | undefined): string => {
    if (!bytes || bytes === 0) {
      return 'Unknown';
    }

    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  return (
    <div className={styles.videoCard}>
      <div className={styles.thumbnail}>
        {video.thumbnail_url ? (
          <img
            src={video.thumbnail_url}
            alt={video.title}
            className={styles.thumbnailImage}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        ) : (
          <div className={styles.placeholderThumbnail}>
            📹
          </div>
        )}
        <div className={styles.duration}>
          {formatDuration(video.duration)}
        </div>
      </div>

      <div className={styles.content}>
        <h3 className={styles.title} title={video.title}>
          {video.title}
        </h3>

        <div className={styles.metadata}>
          <span className={styles.channel}>{video.channel_name}</span>
          <span className={styles.size}>{formatFileSize(video.file_size)}</span>
          {video.view_count && <span className={styles.views}>{video.view_count} views</span>}
        </div>

        {video.description && (
          <p className={styles.description}>{video.description}</p>
        )}

        <div className={styles.actions}>
          <Button
            onClick={() => onPlay(video)}
            variant="primary"
            size="small"
          >
            播放
          </Button>

          {video.subtitle_available && (
            <Button
              onClick={() => onExportSubtitle(video)}
              variant="secondary"
              size="small"
            >
              导出字幕
            </Button>
          )}

          <Button
            onClick={() => onDelete(video)}
            variant="danger"
            size="small"
          >
            删除
          </Button>
        </div>
      </div>
    </div>
  );
};

export default VideoCard;