import React, { useMemo, useEffect, useRef } from 'react';
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
  const historyScrollRef = useRef<HTMLDivElement>(null);

  // Find current subtitle and split into past/current/future
  const { currentSubtitle, pastSubtitles, futureSubtitles, isPreview } = useMemo(() => {
    // Find exact match - subtitle that contains current time
    const currentIndex = subtitles.findIndex(
      segment =>
        currentTime >= segment.start_time &&
        currentTime < segment.end_time
    );

    if (currentIndex !== -1) {
      // Found exact match
      return {
        currentSubtitle: subtitles[currentIndex],
        pastSubtitles: subtitles.slice(0, currentIndex).reverse(),
        futureSubtitles: subtitles.slice(currentIndex + 1),
        isPreview: false,
      };
    }

    // No exact match - find next upcoming subtitle (preview mode)
    const nextIndex = subtitles.findIndex(seg => currentTime < seg.start_time);

    if (nextIndex !== -1) {
      // Show next subtitle as preview
      const previewSubtitle = subtitles[nextIndex];
      const timeUntilStart = previewSubtitle.start_time - currentTime;

      // Only show preview if next subtitle is within 3 seconds
      if (timeUntilStart <= 3) {
        return {
          currentSubtitle: previewSubtitle,
          pastSubtitles: nextIndex > 0 ? subtitles.slice(0, nextIndex).reverse() : [],
          futureSubtitles: subtitles.slice(nextIndex + 1),
          isPreview: true,
        };
      }

      // Next subtitle is too far away, just show past subtitles
      return {
        currentSubtitle: null,
        pastSubtitles: nextIndex > 0 ? subtitles.slice(0, nextIndex).reverse() : [],
        futureSubtitles: subtitles.slice(nextIndex),
        isPreview: false,
      };
    }

    // All subtitles are in the past
    return {
      currentSubtitle: null,
      pastSubtitles: subtitles.slice().reverse(),
      futureSubtitles: [],
      isPreview: false,
    };
  }, [subtitles, currentTime]);

  // Auto-scroll history to top when current subtitle changes
  useEffect(() => {
    if (historyScrollRef.current) {
      historyScrollRef.current.scrollTo({
        top: 0,
        behavior: 'smooth',
      });
    }
  }, [currentSubtitle?.id]);

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
      {/* 当前字幕区域 - 固定在顶部 */}
      {currentSubtitle && (
        <div className={styles.currentSection}>
          {isPreview && (
            <div className={styles.previewBadge}>
              即将播放 ({Math.ceil(currentSubtitle.start_time - currentTime)}s)
            </div>
          )}
          <div
            className={`${styles.subtitleItem} ${isPreview ? styles.preview : styles.active}`}
            data-testid="current-subtitle"
          >
            <div className={styles.timestamp}>
              {formatTime(currentSubtitle.start_time)}
            </div>
            <div className={styles.textContainer}>
              <div
                className={styles.englishSubtitle}
                data-testid="english-subtitle"
              >
                {currentSubtitle.text_english}
              </div>
              {currentSubtitle.text_chinese && (
                <div
                  className={styles.chineseSubtitle}
                  data-testid="chinese-subtitle"
                >
                  {currentSubtitle.text_chinese}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 历史字幕区域 - 可滚动 */}
      {pastSubtitles.length > 0 && (
        <div className={styles.historySection} ref={historyScrollRef}>
          <div className={styles.historyLabel}>已播放字幕</div>
          <div className={styles.subtitleList}>
            {pastSubtitles.map((segment) => (
              <div
                key={segment.id}
                className={`${styles.subtitleItem} ${styles.past}`}
                data-testid={`subtitle-${segment.id}`}
              >
                <div className={styles.timestamp}>
                  {formatTime(segment.start_time)}
                </div>
                <div className={styles.textContainer}>
                  <div className={styles.englishSubtitle}>
                    {segment.text_english}
                  </div>
                  {segment.text_chinese && (
                    <div className={styles.chineseSubtitle}>
                      {segment.text_chinese}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 空状态提示 */}
      {!currentSubtitle && pastSubtitles.length === 0 && (
        <div className={styles.emptyState}>
          {subtitles.length === 0 ? '暂无字幕' : '等待字幕开始...'}
        </div>
      )}
    </div>
  );
};

// Helper function to format time
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

export default SubtitleDisplay;