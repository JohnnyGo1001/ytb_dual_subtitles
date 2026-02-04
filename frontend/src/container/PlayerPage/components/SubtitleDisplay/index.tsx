import React, { useMemo } from 'react';
import type { SubtitleSegment } from '@/types/video';
import styles from './index.module.css';

interface SubtitleDisplayProps {
  subtitles: SubtitleSegment[];
  currentTime: number;
  visible?: boolean;
  className?: string;
}

const SubtitleDisplay: React.FC<SubtitleDisplayProps> = ({
  subtitles,
  currentTime,
  visible = true,
  className,
}) => {
  // Find current subtitle segment
  const currentSubtitle = useMemo(() => {
    return subtitles.find(
      segment =>
        currentTime >= segment.start_time &&
        currentTime < segment.end_time
    );
  }, [subtitles, currentTime]);

  const containerClasses = [
    styles.subtitleDisplay,
    visible ? '' : styles.hidden,
    className,
  ].filter(Boolean).join(' ');

  return (
    <div
      className={containerClasses}
      data-testid="subtitle-display"
    >
      <div className={styles.subtitleContainer}>
        <div
          className={styles.englishSubtitle}
          data-testid="english-subtitle"
          role="status"
          aria-live="polite"
        >
          {currentSubtitle?.text_english || ''}
        </div>

        <div
          className={styles.chineseSubtitle}
          data-testid="chinese-subtitle"
          role="status"
          aria-live="polite"
        >
          {currentSubtitle?.text_chinese || ''}
        </div>
      </div>
    </div>
  );
};

export default SubtitleDisplay;