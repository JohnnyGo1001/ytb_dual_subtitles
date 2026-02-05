import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useApi } from '@/hooks/useApi';
import { apiService } from '@/services/api';
import { VideoPlayer, SubtitleDisplay } from './components';
import Loading from '@/components/Loading';
import type { Video, SubtitleData, PlayerState } from '@/types/video';
import styles from './index.module.css';

function PlayerPage() {
  const { videoId } = useParams<{ videoId: string }>();
  const [currentTime, setCurrentTime] = useState(0);
  const [, setPlayerState] = useState<PlayerState>({
    currentTime: 0,
    duration: 0,
    isPlaying: false,
    volume: 1,
    playbackRate: 1,
    isFullscreen: false,
  });

  // Fetch video data
  const {
    data: video,
    isLoading: videoLoading,
    error: videoError,
    execute: loadVideo,
  } = useApi<Video>();

  // Fetch subtitle data
  const {
    data: subtitleData,
    isLoading: subtitleLoading,
    error: subtitleError,
    execute: loadSubtitles,
  } = useApi<SubtitleData>();

  // Load data on mount
  useEffect(() => {
    if (videoId) {
      loadVideo(() => apiService.getVideo(videoId));
      loadSubtitles(() => apiService.getSubtitles(videoId));
    }
  }, [videoId]);

  // Handle video time updates
  const handleTimeUpdate = useCallback((time: number) => {
    setCurrentTime(time);
  }, []);

  // Handle player state changes
  const handleStateChange = useCallback((state: Partial<PlayerState>) => {
    setPlayerState(prev => ({ ...prev, ...state }));
  }, []);

  // Handle video errors
  const handleVideoError = useCallback((error: Error) => {
    console.error('Video playback error:', error);
  }, []);

  // Retry loading data
  const handleRetry = () => {
    if (videoId) {
      loadVideo(() => apiService.getVideo(videoId));
      loadSubtitles(() => apiService.getSubtitles(videoId));
    }
  };

  // Loading state
  if (videoLoading || subtitleLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingContainer}>
          <Loading size="large" overlay />
          <p className={styles.loadingText}>加载中...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (videoError || subtitleError) {
    return (
      <div className={styles.container}>
        <div className={styles.errorContainer}>
          {videoError && (
            <div className={styles.errorMessage}>
              <h3>加载视频失败</h3>
              <p>{videoError}</p>
            </div>
          )}
          {subtitleError && (
            <div className={styles.errorMessage}>
              <h3>加载字幕失败</h3>
              <p>{subtitleError}</p>
            </div>
          )}
          <button
            className={styles.retryButton}
            onClick={handleRetry}
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  // No video found
  if (!video) {
    return (
      <div className={styles.container}>
        <div className={styles.errorContainer}>
          <h3>视频不存在</h3>
          <p>找不到ID为 {videoId} 的视频</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container} data-testid="player-container">
      <div className={styles.header}>
        <h1 className={styles.title}>{video.title}</h1>
        <div className={styles.metadata}>
          <span className={styles.channel}>{video.channel_name}</span>
          <span className={styles.duration}>
            {Math.floor(video.duration / 60)}:{Math.floor(video.duration % 60).toString().padStart(2, '0')}
          </span>
        </div>
      </div>

      <div className={styles.playerSection}>
        <div className={styles.videoPlayerWrapper}>
          <VideoPlayer
            video={video}
            onTimeUpdate={handleTimeUpdate}
            onStateChange={handleStateChange}
            onError={handleVideoError}
          />
        </div>

        <div className={styles.subtitleSection}>
          <SubtitleDisplay
            subtitles={subtitleData?.segments || []}
            currentTime={currentTime}
          />
        </div>
      </div>
    </div>
  );
}

export default PlayerPage;