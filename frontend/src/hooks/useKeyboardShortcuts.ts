/**
 * Custom hook for handling keyboard shortcuts in the video player
 * Task 4: 播放器交互逻辑 - Keyboard shortcuts support
 */

import { useEffect } from 'react';

export interface PlayerActions {
  togglePlay: () => void;
  seek: (time: number) => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  toggleFullscreen: () => void;
  setPlaybackRate: (rate: number) => void;
  toggleSubtitles: () => void;
}

export interface PlayerState {
  isPlaying: boolean;
  currentTime: number;
  volume: number;
  isMuted: boolean;
  playbackRate: number;
  isFullscreen: boolean;
  subtitlesVisible: boolean;
}

export interface UseKeyboardShortcutsOptions {
  playerActions: PlayerActions;
  playerState: PlayerState;
  enabled?: boolean;
}

// Available playback speeds for cycling
const PLAYBACK_SPEEDS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];

// Volume step for arrow up/down
const VOLUME_STEP = 0.1;

// Seek step for arrow left/right (in seconds)
const SEEK_STEP = 10;

export const useKeyboardShortcuts = ({
  playerActions,
  playerState,
  enabled = true,
}: UseKeyboardShortcutsOptions) => {
  useEffect(() => {
    if (!enabled) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't handle keys when typing in form elements
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement ||
        event.target instanceof HTMLSelectElement
      ) {
        return;
      }

      let handled = false;

      switch (event.code) {
        case 'Space':
          // Toggle play/pause
          playerActions.togglePlay();
          handled = true;
          break;

        case 'ArrowLeft':
          // Rewind 10 seconds
          const newTimeLeft = Math.max(0, playerState.currentTime - SEEK_STEP);
          playerActions.seek(newTimeLeft);
          handled = true;
          break;

        case 'ArrowRight':
          // Fast forward 10 seconds
          const newTimeRight = playerState.currentTime + SEEK_STEP;
          playerActions.seek(newTimeRight);
          handled = true;
          break;

        case 'ArrowUp':
          // Increase volume
          const newVolumeUp = Math.min(1.0, playerState.volume + VOLUME_STEP);
          playerActions.setVolume(Math.round(newVolumeUp * 10) / 10); // Round to 1 decimal
          handled = true;
          break;

        case 'ArrowDown':
          // Decrease volume
          const newVolumeDown = Math.max(0.0, playerState.volume - VOLUME_STEP);
          playerActions.setVolume(Math.round(newVolumeDown * 10) / 10); // Round to 1 decimal
          handled = true;
          break;

        case 'KeyF':
          // Toggle fullscreen
          playerActions.toggleFullscreen();
          handled = true;
          break;

        case 'KeyM':
          // Toggle mute
          playerActions.toggleMute();
          handled = true;
          break;

        case 'KeyC':
          // Toggle subtitles
          playerActions.toggleSubtitles();
          handled = true;
          break;

        case 'KeyS':
          // Cycle playback speed
          const currentSpeedIndex = PLAYBACK_SPEEDS.indexOf(playerState.playbackRate);
          const nextSpeedIndex = (currentSpeedIndex + 1) % PLAYBACK_SPEEDS.length;
          const nextSpeed = PLAYBACK_SPEEDS[nextSpeedIndex];
          playerActions.setPlaybackRate(nextSpeed);
          handled = true;
          break;

        default:
          // Unhandled key - don't prevent default
          break;
      }

      // Prevent default behavior for handled keys
      if (handled) {
        event.preventDefault();
      }
    };

    // Add event listener
    document.addEventListener('keydown', handleKeyDown);

    // Cleanup on unmount
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [playerActions, playerState, enabled]);

  // Return keyboard shortcut mapping for documentation/help
  return {
    shortcuts: {
      Space: 'Play/Pause toggle',
      ArrowLeft: 'Rewind 10 seconds',
      ArrowRight: 'Fast forward 10 seconds',
      ArrowUp: 'Increase volume',
      ArrowDown: 'Decrease volume',
      F: 'Toggle fullscreen',
      M: 'Toggle mute',
      C: 'Toggle subtitles',
      S: 'Cycle playback speed',
    },
  };
};