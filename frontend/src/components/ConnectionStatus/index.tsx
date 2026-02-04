import { useEffect, useState } from 'react';
import { useCommunication } from '@/hooks/useCommunication';
import styles from './index.module.css';

interface ConnectionStatusProps {
  className?: string;
  showLabel?: boolean;
}

function ConnectionStatus({ className, showLabel = true }: ConnectionStatusProps) {
  const { isConnected, mode, error } = useCommunication({
    autoConnect: true,
  });

  // 计算当前连接状态
  const getConnectionState = () => {
    if (error) return 'error';
    if (isConnected) return 'connected';
    return 'disconnected';
  };

  const connectionState = getConnectionState();

  // 简化可见性逻辑：始终显示状态组件，或者可以基于具体需求调整
  // 例如：只在出现错误或断开连接时显示
  // const shouldShowComponent = !isConnected || error !== null;

  // 当前设置为总是显示，便于调试和用户了解连接状态
  const shouldShowComponent = true;

  const getStatusInfo = () => {
    switch (connectionState) {
      case 'connecting':
        return {
          icon: '⏳',
          label: '连接中...',
          color: 'var(--warning)',
        };
      case 'connected':
        return {
          icon: mode === 'websocket' ? '🔌' : (mode === 'polling' ? '🔄' : '✅'),
          label: mode === 'websocket' ? '实时连接' : '已连接',
          color: 'var(--success)',
        };
      case 'error':
        return {
          icon: '❌',
          label: '连接错误',
          color: 'var(--error)',
        };
      default:
        return {
          icon: '🔴',
          label: '未连接',
          color: 'var(--text-muted)',
        };
    }
  };

  const statusInfo = getStatusInfo();

  // 如果不需要显示组件，返回null（现在总是显示）
  if (!shouldShowComponent) {
    return null;
  }

  return (
    <div
      className={`${styles.connectionStatus} ${className || ''}`}
      style={{ color: statusInfo.color }}
      title={`通信状态: ${statusInfo.label} (${mode})`}
    >
      <span className={styles.icon}>{statusInfo.icon}</span>
      {showLabel && (
        <span className={styles.label}>{statusInfo.label}</span>
      )}
    </div>
  );
}

export default ConnectionStatus;