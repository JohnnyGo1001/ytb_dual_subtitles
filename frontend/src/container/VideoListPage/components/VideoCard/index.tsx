import React, { useState, useRef, useEffect } from 'react';
import Button from '@/components/Button';
import type { Video } from '@/types/video';
import { CategorySelector } from '../CategorySelector';
import styles from './index.module.css';

interface VideoCardProps {
  video: Video;
  onPlay: (video: Video) => void;
  onDelete: (video: Video) => void;
  onExportSubtitle: (video: Video) => void;
  onCategoryChange?: (video: Video, newCategory: string) => void;
}

const VideoCard: React.FC<VideoCardProps> = ({
  video,
  onPlay,
  onDelete,
  onExportSubtitle,
  onCategoryChange,
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [showCategorySelector, setShowCategorySelector] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };

    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showMenu]);
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
    <div className={styles.videoCard} onClick={() => onPlay(video)}>
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

        {/* 右上角菜单按钮 */}
        <div className={styles.menuContainer} ref={menuRef}>
          <button
            className={styles.menuButton}
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu(!showMenu);
            }}
            title="更多操作"
          >
            ⋮
          </button>

          {showMenu && (
            <div className={styles.menuDropdown}>
              <button
                className={styles.menuItem}
                onClick={(e) => {
                  e.stopPropagation();
                  setShowMenu(false);
                  setShowCategorySelector(true);
                }}
              >
                🏷️ 移动到分类
              </button>
              {video.subtitle_available && (
                <button
                  className={styles.menuItem}
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowMenu(false);
                    onExportSubtitle(video);
                  }}
                >
                  📥 导出字幕
                </button>
              )}
              <button
                className={`${styles.menuItem} ${styles.danger}`}
                onClick={(e) => {
                  e.stopPropagation();
                  setShowMenu(false);
                  onDelete(video);
                }}
              >
                🗑️ 删除视频
              </button>
            </div>
          )}
        </div>

        {/* 分类选择器 */}
        {showCategorySelector && (
          <div className={styles.categorySelectorWrapper}>
            <CategorySelector
              currentCategory={video.category || '未分类'}
              onSelect={(newCategory) => {
                if (onCategoryChange) {
                  onCategoryChange(video, newCategory);
                }
                setShowCategorySelector(false);
              }}
              onClose={() => setShowCategorySelector(false)}
            />
          </div>
        )}
      </div>

      <div className={styles.content}>
        <h3 className={styles.title} title={video.title}>
          {video.title}
        </h3>

        <div className={styles.metadata}>
          <span className={styles.channel}>{video.channel_name}</span>
          <span className={styles.size}>{formatFileSize(video.file_size)}</span>
        </div>
      </div>
    </div>
  );
};

export default VideoCard;