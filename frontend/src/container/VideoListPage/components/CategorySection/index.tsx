import { useState } from 'react';
import type { Video } from '@/types/video';
import VideoCard from '../VideoCard';
import styles from './index.module.css';

interface CategorySectionProps {
  category: string;
  videos: Video[];
  defaultCollapsed?: boolean;
  onPlay: (video: Video) => void;
  onDelete: (video: Video) => void;
  onExportSubtitle: (video: Video) => void;
  onCategoryChange?: (video: Video, newCategory: string) => void;
}

export function CategorySection({
  category,
  videos,
  defaultCollapsed = false,
  onPlay,
  onDelete,
  onExportSubtitle,
  onCategoryChange,
}: CategorySectionProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  const handleToggle = () => {
    setCollapsed(!collapsed);
  };

  return (
    <div className={styles.categorySection}>
      <div className={styles.categoryHeader} onClick={handleToggle}>
        <div className={styles.categoryInfo}>
          <span className={styles.toggleIcon}>
            {collapsed ? '▶' : '▼'}
          </span>
          <h2 className={styles.categoryName}>{category}</h2>
          <span className={styles.videoCount}>({videos.length})</span>
        </div>
      </div>

      {!collapsed && (
        <div className={styles.categoryContent}>
          <div className={styles.videoGrid}>
            {videos.map((video) => (
              <VideoCard
                key={video.id}
                video={video}
                onPlay={onPlay}
                onDelete={onDelete}
                onExportSubtitle={onExportSubtitle}
                onCategoryChange={onCategoryChange}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
