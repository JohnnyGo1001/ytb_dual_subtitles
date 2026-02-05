import { useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { DownloadForm, RecentVideos } from './components';
import { useApi } from '@/hooks/useApi';
import { ToastContext } from '@/contexts/ToastContext';
import { apiService } from '@/services/api';
import type { DownloadTask } from '@/types/api';
import styles from './index.module.css';

function DownloadPage() {
  const navigate = useNavigate();
  const toastContext = useContext(ToastContext);
  const showToast = toastContext?.showToast || (() => {});
  const [activeTasks, setActiveTasks] = useState<DownloadTask[]>([]);
  const [recentTasks, setRecentTasks] = useState<DownloadTask[]>([]);
  const [isConnected, setIsConnected] = useState(true);
  const [isInitialLoad, setIsInitialLoad] = useState(true); // Track if this is the first load

  // API hooks
  const {
    execute: fetchRecentDownloads,
    isLoading: isLoadingRecent,
    error: recentError,
  } = useApi();

  const {
    execute: fetchActiveDownloads,
  } = useApi();

  // Load active downloads from API
  const loadActiveDownloads = useCallback(async () => {
    try {
      const response = await fetchActiveDownloads(async () => {
        // Directly use fetch since we need the exact API endpoint
        const res = await fetch('/api/list/downloads');
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        const responseData = await res.json();
        console.log("/api/list/downloads response======", responseData);
        return responseData;
      });

      // Handle different response formats
      console.log('Full response object:', response);
      let taskData;
      if (response?.success !== undefined) {
        // Standard ApiResponse format
        taskData = response.success ? response.data : [];
      } else if (Array.isArray(response)) {
        // Direct array response
        taskData = response;
      } else {
        // Empty or unexpected format
        console.warn('Unexpected response format:', response);
        taskData = [];
      }

      console.log('Processed taskData:', taskData);
      if (taskData && Array.isArray(taskData)) {
        // 只显示活动状态的任务，排除错误和失败的任务
        const activeTasks = taskData.filter(task =>
          task.status === 'downloading' ||
          task.status === 'pending' ||
          task.status === 'processing'
        );

        setActiveTasks(prevTasks => {
          // On initial load, always use server data
          if (isInitialLoad) {
            setIsInitialLoad(false);
            // Map all active tasks from server
            return activeTasks.map(apiTask => ({
              id: apiTask.task_id,
              title: apiTask.title || '正在获取视频信息...',
              url: apiTask.url,
              status: apiTask.status,
              progress: apiTask.progress || 0,
              downloadedSize: apiTask.downloaded_bytes,
              speed: apiTask.download_speed,
              estimatedTimeRemaining: apiTask.eta_seconds,
              error: apiTask.error_message,
              createdAt: apiTask.created_at,
              updatedAt: apiTask.last_updated,
            }));
          }

          // After initial load, merge with existing tasks
          const existingTasksMap = new Map(prevTasks.map(task => [task.id, task]));

          // Update existing tasks and add new ones from server
          const updatedTasks = activeTasks.map(apiTask => {
            const existingTask = existingTasksMap.get(apiTask.task_id);

            if (existingTask) {
              // Update existing task
              return {
                ...existingTask,
                title: apiTask.title || existingTask.title || '正在获取视频信息...',
                status: apiTask.status,
                progress: apiTask.progress || existingTask.progress,
                downloadedSize: apiTask.downloaded_bytes,
                speed: apiTask.download_speed,
                estimatedTimeRemaining: apiTask.eta_seconds,
                error: apiTask.error_message,
              };
            } else {
              // New task from server
              return {
                id: apiTask.task_id,
                title: apiTask.title || '正在获取视频信息...',
                url: apiTask.url,
                status: apiTask.status,
                progress: apiTask.progress || 0,
                downloadedSize: apiTask.downloaded_bytes,
                speed: apiTask.download_speed,
                estimatedTimeRemaining: apiTask.eta_seconds,
                error: apiTask.error_message,
                createdAt: apiTask.created_at,
                updatedAt: apiTask.last_updated,
              };
            }
          });

          return updatedTasks;
        });

        setIsConnected(true);
      }
    } catch (error) {
      console.error('Failed to load active downloads:', error);
      setIsConnected(false);
    }
  }, [fetchActiveDownloads, isInitialLoad]);

  // Load recent downloads
  const loadRecentDownloads = useCallback(async () => {
    try {
      const response = await fetchRecentDownloads(() =>
        apiService.getDownloads()
      );

      console.log('最近下载API响应:', response); // 调试日志

      // If response is null, it means the API call failed
      if (response === null) {
        console.warn('API call returned null');
        setRecentTasks([]);
        return;
      }

      // useApi.execute returns the unwrapped data, so it should be an array
      if (Array.isArray(response)) {
        console.log('直接数组响应，包含', response.length, '个任务');

        // 过滤已完成的任务
        const completedApiTasks = response.filter(task => task.status === 'completed');
        console.log('已完成的API任务原始数据:', completedApiTasks);

        // 检查第一个任务的所有字段
        if (completedApiTasks.length > 0) {
          console.log('第一个已完成任务的所有字段:', Object.keys(completedApiTasks[0]));
          console.log('第一个已完成任务的完整内容:', completedApiTasks[0]);
        }

        // 映射为前端格式
        const completedTasks = completedApiTasks.map(apiTask => ({
          id: apiTask.task_id,
          title: apiTask.title || apiTask.video_title || apiTask.name || apiTask.video_name || apiTask.filename || '未知标题',
          url: apiTask.url,
          status: apiTask.status,
          progress: apiTask.progress || 0,
          createdAt: apiTask.created_at || new Date().toISOString(),
          updatedAt: apiTask.updated_at || apiTask.last_updated || new Date().toISOString(),
        } as DownloadTask));

        console.log('映射后的已完成任务:', completedTasks);
        setRecentTasks(completedTasks);
      } else {
        console.warn('未识别的响应格式:', response);
        setRecentTasks([]);
      }
    } catch (error) {
      console.error('Failed to load recent downloads:', error);
      setRecentTasks([]);
    }
  }, [fetchRecentDownloads]);

  // Load initial data on component mount
  useEffect(() => {
    loadRecentDownloads();
    loadActiveDownloads(); // 恢复加载活动任务
  }, [loadRecentDownloads, loadActiveDownloads]);

  // Set up polling for active downloads
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    // Count truly active tasks (exclude failed/error which will be cleaned up)
    const activeCount = activeTasks.filter(task =>
      task.status === 'downloading' ||
      task.status === 'pending' ||
      task.status === 'processing'
    ).length;

    // Poll if there are active tasks OR if we just loaded the page (to check for background tasks)
    if (activeCount > 0 || isInitialLoad) {
      intervalId = setInterval(() => {
        loadActiveDownloads();
      }, 2000); // Poll every 2 seconds
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [activeTasks, loadActiveDownloads, isInitialLoad]);

  // Keep error/failed tasks visible until user manually dismisses them
  // (Removed automatic cleanup to allow users to see error details)

  // Handle download start
  const handleDownloadStart = useCallback((task: DownloadTask) => {
    console.log('handleDownloadStart called with task:', task);
    showToast('下载任务已创建，正在后台下载', 'success');

    // Mark that we're no longer in initial load state
    setIsInitialLoad(false);

    // Add new task to active tasks immediately for instant feedback
    setActiveTasks(prev => [...prev, task]);

    // Refresh from server to get accurate status
    setTimeout(() => {
      loadActiveDownloads();
    }, 500);
  }, [showToast, loadActiveDownloads]);

  // Handle task cancellation
  const handleCancelTask = useCallback(async (taskId: string) => {
    try {
      await apiService.cancelDownload(taskId);
      setActiveTasks(prev => prev.filter(task => task.id !== taskId));
      showToast('下载任务已取消', 'info');
    } catch (error) {
      console.error('Failed to cancel download:', error);
      showToast('取消下载失败', 'error');
    }
  }, [showToast]);

  // Handle task click (navigate to details or video list)
  const handleTaskClick = useCallback((task: DownloadTask) => {
    if (task.status === 'completed') {
      navigate('/');
    }
  }, [navigate]);

  // Error is now shown inline, no need for toast

  return (
    <div className={styles.container}>
      {!isConnected && (
        <div className={styles.connectionWarning}>
          ⚠️ 实时进度更新已断开，请检查服务器连接
        </div>
      )}

      {activeTasks.length > 0 && (
        <div className={styles.infoBar}>
          <span className={styles.infoText}>
            📥 {activeTasks.length} 个任务正在后台下载，自动每2秒更新进度
          </span>
          <button
            onClick={() => loadActiveDownloads()}
            className={styles.refreshButton}
            title="立即刷新进度"
          >
            🔄 刷新
          </button>
        </div>
      )}

      <div className={styles.downloadSection}>
        <DownloadForm onDownloadStart={handleDownloadStart} activeTasks={activeTasks} />
      </div>

      {/* Active downloads */}
      {activeTasks.length > 0 && (
        <div className={styles.activeSection}>
          <h2 className={styles.sectionTitle}>
            当前下载
            <span className={styles.asyncHint}>（任务在后台异步执行，页面刷新后仍会继续）</span>
          </h2>
          <div className={styles.activeTasksList}>
            {activeTasks.map((task, index) => (
              <div key={`task-${task.id}-${index}`} className={styles.activeTask}>
                {/* We can reuse ProgressCard or create a simpler version */}
                <div className={styles.taskInfo}>
                  <h4>{task.title || '正在获取视频信息...'}</h4>
                  <div className={styles.progressBar}>
                    <div
                      className={styles.progressFill}
                      style={{ width: `${task.progress}%` }}
                    />
                  </div>
                  <div className={styles.taskMeta}>
                    <span>{task.progress}%</span>
                    <span>{task.status}</span>
                    <button
                      onClick={() => handleCancelTask(task.id)}
                      className={styles.cancelButton}
                    >
                      取消
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className={styles.recentSection}>
        {recentError && (
          <div className={styles.errorMessage}>
            ⚠️ 加载最近下载失败：{recentError}
            <button
              onClick={() => loadRecentDownloads()}
              className={styles.retryButton}
            >
              重试
            </button>
          </div>
        )}
        <RecentVideos
          tasks={recentTasks}
          loading={isLoadingRecent}
          maxItems={5}
          showViewAll={true}
          onTaskClick={handleTaskClick}
          onCancelTask={handleCancelTask}
        />
      </div>
    </div>
  );
}

export default DownloadPage;