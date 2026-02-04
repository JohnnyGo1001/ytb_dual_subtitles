/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  const size = bytes / Math.pow(k, i);
  const formattedSize = i === 0 ? size.toString() : size.toFixed(1);

  return `${formattedSize} ${sizes[i]}`;
}

/**
 * 格式化下载速度
 */
export function formatDownloadSpeed(bytesPerSecond: number): string {
  if (bytesPerSecond === 0) return '0 B/s';

  const k = 1024;
  const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
  const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k));

  const speed = bytesPerSecond / Math.pow(k, i);
  const formattedSpeed = i === 0 ? speed.toString() : speed.toFixed(1);

  return `${formattedSpeed} ${sizes[i]}`;
}

/**
 * 格式化时间（秒转为 HH:MM:SS）
 */
export function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return '00:00';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  } else {
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }
}

/**
 * 格式化剩余时间（秒转为易读格式）
 */
export function formatETA(seconds: number): string {
  if (!seconds || seconds <= 0) return '--';

  if (seconds < 60) {
    return `${Math.ceil(seconds)}秒`;
  } else if (seconds < 3600) {
    const minutes = Math.ceil(seconds / 60);
    return `${minutes}分钟`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.ceil((seconds % 3600) / 60);
    if (minutes === 0) {
      return `${hours}小时`;
    }
    return `${hours}小时${minutes}分钟`;
  }
}

/**
 * 格式化日期时间
 */
export function formatDateTime(dateString: string): string {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    // 如果是今天
    if (diffDays === 0) {
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      });
    }
    // 如果是昨天
    else if (diffDays === 1) {
      return `昨天 ${date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      })}`;
    }
    // 如果是一周内
    else if (diffDays < 7) {
      return `${diffDays}天前`;
    }
    // 其他情况显示完整日期
    else {
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    }
  } catch {
    return dateString;
  }
}

/**
 * 格式化百分比
 */
export function formatPercent(value: number): string {
  return `${Math.round(value)}%`;
}

/**
 * 截断长文本
 */
export function truncateText(text: string, maxLength: number): string {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

/**
 * 格式化下载状态显示文本
 */
export function formatDownloadStatus(status: string): string {
  const statusMap: Record<string, string> = {
    pending: '等待中',
    downloading: '下载中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  };

  return statusMap[status] || status;
}

/**
 * 格式化视频标题（清理特殊字符）
 */
export function sanitizeVideoTitle(title: string): string {
  if (!title) return '未知标题';

  // 移除或替换文件系统不支持的字符
  return title
    .replace(/[<>:"/\\|?*]/g, '_')
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 100); // 限制长度
}

/**
 * 格式化日期（简化版本，用于视频卡片）
 */
export function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateString;
  }
}