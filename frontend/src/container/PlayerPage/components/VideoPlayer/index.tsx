import React, { useRef, useEffect, useState, useCallback } from 'react';
import type { Video, PlayerState } from '@/types/video';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import styles from './index.module.css';

interface VideoPlayerProps {
  video: Video;
  onTimeUpdate?: (currentTime: number) => void;
  onStateChange?: (state: Partial<PlayerState>) => void;
  onError?: (error: Error) => void;
  keyboardShortcuts?: boolean;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({
  video,
  onTimeUpdate,
  onStateChange,
  onError,
  keyboardShortcuts = true,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playerState, setPlayerState] = useState<PlayerState>({
    currentTime: 0,
    duration: 0,
    isPlaying: false,
    volume: 1,
    playbackRate: 1,
    isFullscreen: false,
  });

  const [subtitlesVisible, setSubtitlesVisible] = useState(true);

  // Update internal state and notify parent
  const updateState = useCallback((newState: Partial<PlayerState>) => {
    setPlayerState(prev => {
      const updated = { ...prev, ...newState };
      // Call onStateChange outside of render, but we don't include it in deps
      // to avoid infinite loops since parent might recreate the callback
      return updated;
    });
  }, []);

  // Notify parent of state changes after component updates
  useEffect(() => {
    if (onStateChange) {
      onStateChange(playerState);
    }
    // Intentionally not including onStateChange in deps to prevent infinite loop
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playerState.currentTime, playerState.duration, playerState.isPlaying, playerState.volume, playerState.playbackRate, playerState.isFullscreen]);

  // Play/Pause toggle
  const togglePlay = async () => {
    if (!videoRef.current) return;

    try {
      if (playerState.isPlaying) {
        videoRef.current.pause();
        updateState({ isPlaying: false });
      } else {
        await videoRef.current.play();
        updateState({ isPlaying: true });
      }
    } catch (error) {
      onError?.(error as Error);
    }
  };

  // Handle time update
  const handleTimeUpdate = useCallback(() => {
    if (!videoRef.current) return;
    const currentTime = videoRef.current.currentTime;
    updateState({ currentTime });
    onTimeUpdate?.(currentTime);
  }, [updateState, onTimeUpdate]);

  // Handle loaded metadata
  const handleLoadedMetadata = useCallback(() => {
    if (!videoRef.current) return;
    const duration = videoRef.current.duration;
    updateState({ duration, isPlaying: false });
  }, [updateState]);

  // Handle progress change
  const handleProgressChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!videoRef.current) return;
    const newTime = parseFloat(event.target.value);
    videoRef.current.currentTime = newTime;
    updateState({ currentTime: newTime });
  };

  // Handle volume change
  const handleVolumeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!videoRef.current) return;
    const newVolume = parseFloat(event.target.value);
    videoRef.current.volume = newVolume;
    updateState({ volume: newVolume });
  };

  // Seek to specific time
  const seekTo = (time: number) => {
    if (!videoRef.current) return;
    const clampedTime = Math.max(0, Math.min(time, playerState.duration));
    videoRef.current.currentTime = clampedTime;
    updateState({ currentTime: clampedTime });
  };

  // Set volume
  const setVolume = (volume: number) => {
    if (!videoRef.current) return;
    const clampedVolume = Math.max(0, Math.min(volume, 1));
    videoRef.current.volume = clampedVolume;
    updateState({ volume: clampedVolume });
  };

  // Toggle mute
  const toggleMute = () => {
    if (!videoRef.current) return;

    if (playerState.volume > 0) {
      // Mute: save current volume and set to 0
      videoRef.current.volume = 0;
      updateState({ volume: 0 });
    } else {
      // Unmute: restore to default volume
      videoRef.current.volume = 1;
      updateState({ volume: 1 });
    }
  };

  // Set playback rate
  const setPlaybackRate = (rate: number) => {
    if (!videoRef.current) return;
    const clampedRate = Math.max(0.25, Math.min(rate, 4.0));
    videoRef.current.playbackRate = clampedRate;
    updateState({ playbackRate: clampedRate });
  };

  // Toggle subtitles
  const toggleSubtitles = () => {
    setSubtitlesVisible(prev => !prev);
  };

  // Handle fullscreen toggle
  const toggleFullscreen = () => {
    if (!videoRef.current) return;

    if (!document.fullscreenElement) {
      videoRef.current.requestFullscreen().then(() => {
        updateState({ isFullscreen: true });
      }).catch((error) => {
        onError?.(error);
      });
    } else {
      document.exitFullscreen().then(() => {
        updateState({ isFullscreen: false });
      }).catch((error) => {
        onError?.(error);
      });
    }
  };

  // Handle video error
  const handleError = useCallback(() => {
    if (!videoRef.current) return;
    const error = new Error(`视频加载失败: ${video.title}`);
    onError?.(error);
  }, [video.title, onError]);

  // Format time for display
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Setup keyboard shortcuts
  const keyboardShortcutsResult = useKeyboardShortcuts({
    playerActions: {
      togglePlay,
      seek: seekTo,
      setVolume,
      toggleMute,
      toggleFullscreen,
      setPlaybackRate,
      toggleSubtitles,
    },
    playerState: {
      ...playerState,
      subtitlesVisible,
      isMuted: playerState.volume === 0,
    },
    enabled: keyboardShortcuts,
  });

  useEffect(() => {
    const videoElement = videoRef.current;
    if (!videoElement) return;

    // Set initial volume
    videoElement.volume = playerState.volume;

    // Event listeners
    videoElement.addEventListener('timeupdate', handleTimeUpdate);
    videoElement.addEventListener('loadedmetadata', handleLoadedMetadata);
    videoElement.addEventListener('error', handleError);

    return () => {
      videoElement.removeEventListener('timeupdate', handleTimeUpdate);
      videoElement.removeEventListener('loadedmetadata', handleLoadedMetadata);
      videoElement.removeEventListener('error', handleError);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [handleTimeUpdate, handleLoadedMetadata, handleError]);

  return (
    <div className={styles.videoPlayer}>
      <video
        ref={videoRef}
        src={video.download_url}
        className={styles.video}
        controls={false}
        role="video"
      />

      <div className={styles.controls}>
        <button
          className={styles.playButton}
          onClick={togglePlay}
          aria-label={playerState.isPlaying ? '暂停' : '播放'}
        >
          {playerState.isPlaying ? '⏸️' : '▶️'}
        </button>

        <input
          type="range"
          className={styles.progressBar}
          min="0"
          max={playerState.duration || 0}
          value={playerState.currentTime}
          onChange={handleProgressChange}
          aria-label="播放进度"
        />

        <span className={styles.timeDisplay}>
          {formatTime(playerState.currentTime)} / {formatTime(playerState.duration)}
        </span>

        <input
          type="range"
          className={styles.volumeControl}
          min="0"
          max="1"
          step="0.1"
          value={playerState.volume}
          onChange={handleVolumeChange}
          aria-label="音量"
        />

        <button
          className={styles.fullscreenButton}
          onClick={toggleFullscreen}
          aria-label="全屏"
        >
          ⛶
        </button>
      </div>
    </div>
  );
};

export default VideoPlayer;