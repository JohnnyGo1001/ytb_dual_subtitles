import { createContext, useContext, useReducer, ReactNode } from 'react';
import type { DownloadTask, ProgressUpdate } from '@/types/api';

// 下载状态定义
export interface DownloadState {
  tasks: DownloadTask[];
  activeTasks: string[];
  recentTasks: DownloadTask[];
}

// 初始状态
const initialState: DownloadState = {
  tasks: [],
  activeTasks: [],
  recentTasks: [],
};

// Action类型定义
export type DownloadAction =
  | { type: 'ADD_TASK'; payload: DownloadTask }
  | { type: 'UPDATE_TASK'; payload: { taskId: string; updates: Partial<DownloadTask> } }
  | { type: 'REMOVE_TASK'; payload: string }
  | { type: 'UPDATE_PROGRESS'; payload: ProgressUpdate }
  | { type: 'SET_TASKS'; payload: DownloadTask[] }
  | { type: 'CLEAR_COMPLETED' };

// Reducer
function downloadReducer(state: DownloadState, action: DownloadAction): DownloadState {
  switch (action.type) {
    case 'ADD_TASK': {
      const newTask = action.payload;
      const updatedTasks = [...state.tasks, newTask];
      const updatedActiveTasks = newTask.status === 'pending' || newTask.status === 'downloading'
        ? [...state.activeTasks, newTask.id]
        : state.activeTasks;

      return {
        ...state,
        tasks: updatedTasks,
        activeTasks: updatedActiveTasks,
        recentTasks: [newTask, ...state.recentTasks].slice(0, 10), // 保持最近10个
      };
    }

    case 'UPDATE_TASK': {
      const { taskId, updates } = action.payload;
      const updatedTasks = state.tasks.map(task =>
        task.id === taskId ? { ...task, ...updates, updated_at: new Date().toISOString() } : task
      );

      // 更新活跃任务列表
      let updatedActiveTasks = state.activeTasks;
      if (updates.status && (updates.status === 'completed' || updates.status === 'failed' || updates.status === 'cancelled')) {
        updatedActiveTasks = state.activeTasks.filter(id => id !== taskId);
      } else if (updates.status && (updates.status === 'pending' || updates.status === 'downloading')) {
        if (!state.activeTasks.includes(taskId)) {
          updatedActiveTasks = [...state.activeTasks, taskId];
        }
      }

      return {
        ...state,
        tasks: updatedTasks,
        activeTasks: updatedActiveTasks,
        recentTasks: updatedTasks.filter(task =>
          task.status === 'completed' || task.status === 'failed'
        ).slice(0, 10),
      };
    }

    case 'UPDATE_PROGRESS': {
      const progressUpdate = action.payload;
      return downloadReducer(state, {
        type: 'UPDATE_TASK',
        payload: {
          taskId: progressUpdate.task_id,
          updates: {
            progress: progressUpdate.progress,
            status: progressUpdate.status as DownloadTask['status'],
            fileSize: progressUpdate.total_size,
            downloadedSize: progressUpdate.downloaded_size,
            speed: progressUpdate.speed,
            estimatedTimeRemaining: progressUpdate.eta,
            error: progressUpdate.error,
          },
        },
      });
    }

    case 'REMOVE_TASK': {
      const taskId = action.payload;
      return {
        ...state,
        tasks: state.tasks.filter(task => task.id !== taskId),
        activeTasks: state.activeTasks.filter(id => id !== taskId),
        recentTasks: state.recentTasks.filter(task => task.id !== taskId),
      };
    }

    case 'SET_TASKS': {
      const tasks = action.payload;
      const activeTasks = tasks
        .filter(task => task.status === 'pending' || task.status === 'downloading')
        .map(task => task.id);
      const recentTasks = tasks
        .filter(task => task.status === 'completed' || task.status === 'failed')
        .slice(0, 10);

      return {
        tasks,
        activeTasks,
        recentTasks,
      };
    }

    case 'CLEAR_COMPLETED': {
      const activeTasks = state.tasks.filter(
        task => task.status === 'pending' || task.status === 'downloading'
      );
      return {
        ...state,
        tasks: activeTasks,
        recentTasks: [],
      };
    }

    default:
      return state;
  }
}

// Context类型定义
interface DownloadContextType {
  state: DownloadState;
  dispatch: React.Dispatch<DownloadAction>;
}

// 创建Context
const DownloadContext = createContext<DownloadContextType | undefined>(undefined);

// Provider组件
interface DownloadProviderProps {
  children: ReactNode;
}

export function DownloadProvider({ children }: DownloadProviderProps) {
  const [state, dispatch] = useReducer(downloadReducer, initialState);

  return (
    <DownloadContext.Provider value={{ state, dispatch }}>
      {children}
    </DownloadContext.Provider>
  );
}

// 自定义Hook
export function useDownload() {
  const context = useContext(DownloadContext);
  if (context === undefined) {
    throw new Error('useDownload must be used within a DownloadProvider');
  }
  return context;
}