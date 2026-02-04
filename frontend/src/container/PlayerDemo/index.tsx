import { useState } from 'react';
import { VideoPlayer, SubtitleDisplay } from '@/container/PlayerPage/components';
import type { Video, SubtitleSegment, PlayerState } from '@/types/video';
import styles from './index.module.css';

// 演示数据
const demoVideo: Video = {
  id: 'demo-video',
  title: '演示视频：播放器功能展示',
  description: '这是一个演示视频，展示播放器的各项功能',
  youtube_id: 'demo-youtube-id',
  duration: 120,
  thumbnail_url: '/demo-thumbnail.jpg',
  file_path: '/demo/video.mp4',
  file_size: 52428800, // 50MB
  download_url: '/demo/sample-video.mp4',
  subtitle_available: true,
  view_count: 1000,
  upload_date: '2024-02-01',
  channel_name: 'Tech Demo Channel',
  created_at: '2024-02-01T12:00:00Z',
  updated_at: '2024-02-01T12:00:00Z',
};

const demoSubtitles: SubtitleSegment[] = [
  {
    id: 'demo-1',
    video_id: 'demo-video',
    start_time: 0,
    end_time: 5,
    text_english: 'Welcome to the video player demo',
    text_chinese: '欢迎来到视频播放器演示',
    sequence: 1,
  },
  {
    id: 'demo-2',
    video_id: 'demo-video',
    start_time: 5,
    end_time: 10,
    text_english: 'This player supports dual language subtitles',
    text_chinese: '这个播放器支持双语字幕',
    sequence: 2,
  },
  {
    id: 'demo-3',
    video_id: 'demo-video',
    start_time: 10,
    end_time: 15,
    text_english: 'You can control playback speed and volume',
    text_chinese: '你可以控制播放速度和音量',
    sequence: 3,
  },
  {
    id: 'demo-4',
    video_id: 'demo-video',
    start_time: 15,
    end_time: 20,
    text_english: 'Fullscreen mode is also supported',
    text_chinese: '还支持全屏模式',
    sequence: 4,
  },
];

function PlayerDemo() {
  const [currentTime, setCurrentTime] = useState(0);
  const [playerState, setPlayerState] = useState<PlayerState>({
    currentTime: 0,
    duration: 0,
    isPlaying: false,
    volume: 1,
    playbackRate: 1,
    isFullscreen: false,
  });

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time);
  };

  const handleStateChange = (state: Partial<PlayerState>) => {
    setPlayerState(prev => ({ ...prev, ...state }));
  };

  const handleError = (error: Error) => {
    console.error('播放器错误:', error);
    alert(`播放器错误: ${error.message}`);
  };

  return (
    <div className={styles.demoContainer}>
      <div className={styles.header}>
        <h1 className={styles.title}>播放器功能演示</h1>
        <p className={styles.description}>
          这是一个功能完整的HTML5视频播放器，支持双语字幕同步显示、播放控制和响应式设计。
        </p>
      </div>

      <div className={styles.playerSection}>
        <div className={styles.videoSection}>
          <h2 className={styles.sectionTitle}>{demoVideo.title}</h2>
          <div className={styles.metadata}>
            <span className={styles.channel}>{demoVideo.channel_name}</span>
            <span className={styles.duration}>
              {Math.floor(demoVideo.duration / 60)}:{Math.floor(demoVideo.duration % 60).toString().padStart(2, '0')}
            </span>
          </div>

          <div className={styles.playerWrapper}>
            <VideoPlayer
              video={demoVideo}
              onTimeUpdate={handleTimeUpdate}
              onStateChange={handleStateChange}
              onError={handleError}
            />
          </div>
        </div>

        <div className={styles.subtitleSection}>
          <h3 className={styles.sectionTitle}>实时字幕显示</h3>
          <SubtitleDisplay
            subtitles={demoSubtitles}
            currentTime={currentTime}
          />
        </div>
      </div>

      <div className={styles.infoSection}>
        <h3 className={styles.sectionTitle}>播放器状态</h3>
        <div className={styles.stateInfo}>
          <div className={styles.stateItem}>
            <strong>播放状态:</strong> {playerState.isPlaying ? '播放中' : '暂停'}
          </div>
          <div className={styles.stateItem}>
            <strong>当前时间:</strong> {Math.floor(currentTime)}秒
          </div>
          <div className={styles.stateItem}>
            <strong>视频时长:</strong> {Math.floor(playerState.duration)}秒
          </div>
          <div className={styles.stateItem}>
            <strong>音量:</strong> {Math.round(playerState.volume * 100)}%
          </div>
          <div className={styles.stateItem}>
            <strong>全屏状态:</strong> {playerState.isFullscreen ? '全屏' : '窗口'}
          </div>
        </div>
      </div>

      <div className={styles.featuresSection}>
        <h3 className={styles.sectionTitle}>功能特点</h3>
        <div className={styles.features}>
          <div className={styles.feature}>
            <h4>🎥 HTML5视频播放</h4>
            <p>基于原生HTML5 video元素，支持多种视频格式</p>
          </div>
          <div className={styles.feature}>
            <h4>🌐 双语字幕</h4>
            <p>实时显示中英文字幕，精确同步（±100ms）</p>
          </div>
          <div className={styles.feature}>
            <h4>🎮 完整控制</h4>
            <p>播放/暂停、进度条、音量、全屏等完整功能</p>
          </div>
          <div className={styles.feature}>
            <h4>📱 响应式设计</h4>
            <p>支持桌面和移动设备，自适应屏幕尺寸</p>
          </div>
          <div className={styles.feature}>
            <h4>🎨 主题适配</h4>
            <p>支持深色和浅色主题，现代化UI设计</p>
          </div>
          <div className={styles.feature}>
            <h4>⚡ 高性能</h4>
            <p>优化的字幕查找算法，流畅的播放体验</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PlayerDemo;