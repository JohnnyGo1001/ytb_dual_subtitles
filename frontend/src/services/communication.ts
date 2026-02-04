/**
 * 统一的通信服务 - 使用 HTTP 轮询模式
 * Unified Communication Service - HTTP polling mode
 */

export interface CommunicationMessage {
  type: string;
  data: any;
  timestamp?: string;
}

export interface ProgressData {
  task_id: string;
  progress: number;
  status: string;
  downloaded_bytes?: number;
  total_bytes?: number;
  download_speed?: number;
  eta_seconds?: number;
  error?: string;
}

export interface CommunicationOptions {
  baseUrl?: string;
  pollingInterval?: number;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
}

export type CommunicationMode = 'polling';

export class CommunicationService {
  private static instance: CommunicationService | null = null;

  private mode: CommunicationMode = 'polling';
  private options: Required<CommunicationOptions>;
  private listeners: Map<string, Array<(data: any) => void>> = new Map();
  private connectionState: 'connecting' | 'connected' | 'disconnected' | 'error' = 'disconnected';

  // HTTP Polling specific
  private reconnectAttempts = 0;
  private reconnectTimeoutId: number | null = null;
  private shouldReconnect = true;
  private pollingIntervalId: number | null = null;
  private isPolling = false;

  private constructor(options: CommunicationOptions = {}) {
    this.options = {
      baseUrl: options.baseUrl || 'http://localhost:8000',
      pollingInterval: options.pollingInterval || 2000,
      maxReconnectAttempts: options.maxReconnectAttempts || 5,
      reconnectInterval: options.reconnectInterval || 3000,
    };
  }

  public static getInstance(options?: CommunicationOptions): CommunicationService {
    if (!CommunicationService.instance) {
      CommunicationService.instance = new CommunicationService(options);
    }
    return CommunicationService.instance;
  }

  /**
   * 使用 HTTP 轮询模式连接
   */
  public async connect(): Promise<void> {
    if (this.connectionState === 'connected') {
      return;
    }

    this.connectionState = 'connecting';
    this.shouldReconnect = true;

    try {
      console.log('Using HTTP polling mode');
      this.mode = 'polling';
      await this.startPolling();
    } catch (error) {
      console.error('Failed to establish HTTP polling communication:', error);
      this.connectionState = 'error';
      throw error;
    }
  }



  /**
   * 开始 HTTP 轮询
   */
  private async startPolling(): Promise<void> {
    if (this.isPolling) {
      return;
    }

    this.isPolling = true;
    this.connectionState = 'connecting'; // 开始时设为连接中

    const poll = async () => {
      try {
        const response = await fetch(`${this.getHttpBaseUrl()}/api/status`);

        if (response.ok) {
          const data = await response.json();

          // 第一次成功请求后设置为已连接
          if (this.connectionState !== 'connected') {
            this.connectionState = 'connected';
            console.log("轮询连接状态更新为: connected");
            // 通知状态变化
            this.notifyListeners('connection_status_changed', {
              state: 'connected',
              mode: 'polling'
            });
          }

          this.handlePollingData(data);
        } else {
          console.warn(`API status returned ${response.status}: ${response.statusText}`);
          // 请求失败但不一定是致命错误
          if (this.connectionState === 'connecting') {
            this.connectionState = 'error';
            this.notifyListeners('connection_status_changed', {
              state: 'error',
              mode: 'polling'
            });
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
        this.handlePollingError();
      }
    };

    // 立即执行一次
    await poll();

    // 设置定时轮询
    this.pollingIntervalId = window.setInterval(poll, this.options.pollingInterval);
  }

  /**
   * 停止连接
   */
  public disconnect(): void {
    this.shouldReconnect = false;

    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    if (this.pollingIntervalId) {
      clearInterval(this.pollingIntervalId);
      this.pollingIntervalId = null;
      this.isPolling = false;
    }

    this.connectionState = 'disconnected';
  }

  /**
   * 订阅消息
   */
  public subscribe(messageType: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(messageType)) {
      this.listeners.set(messageType, []);
    }

    this.listeners.get(messageType)!.push(callback);

    // 返回取消订阅函数
    return () => {
      const callbacks = this.listeners.get(messageType);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index !== -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }

  /**
   * 发送消息（HTTP 轮询模式不支持主动发送消息）
   */
  public send(message: CommunicationMessage): void {
    console.warn('Cannot send message: HTTP polling mode does not support sending messages');
  }

  /**
   * 获取连接状态
   */
  public getConnectionState(): string {
    return this.connectionState;
  }

  /**
   * 获取通信模式
   */
  public getMode(): CommunicationMode {
    return this.mode;
  }

  /**
   * 是否已连接
   */
  public isConnected(): boolean {
    return this.connectionState === 'connected' && this.isPolling;
  }

  // Private helper methods


  private getHttpBaseUrl(): string {
    const baseUrl = this.options.baseUrl;
    if (baseUrl.startsWith('ws://') || baseUrl.startsWith('wss://')) {
      // Convert WS(S) to HTTP(S)
      return baseUrl.replace(/^ws/, 'http');
    }
    return baseUrl;
  }


  private handlePollingData(data: any): void {
    try {

      // 数据为空或无效
      if (!data) {
        console.log('No polling data received');
        return;
      }

      // 如果数据是数组格式（任务列表）
      if (Array.isArray(data)) {
        console.log(`Processing ${data.length} tasks from array`);
        data.forEach((task, index) => {
          try {
            this.processTaskData(task);
          } catch (error) {
            console.error(`Error processing task ${index}:`, error, task);
          }
        });
        return;
      }

      // 如果数据有 tasks 字段且是数组
      if (data && typeof data === 'object' && data.tasks && Array.isArray(data.tasks)) {
        console.log(`Processing ${data.tasks.length} tasks from data.tasks`);
        data.tasks.forEach((task: any, index: number) => {
          try {
            this.processTaskData(task);
          } catch (error) {
            console.error(`Error processing task ${index}:`, error, task);
          }
        });
        return;
      }

      // 如果是单个任务对象
      if (data && typeof data === 'object' && (data.task_id || data.status)) {
        console.log('Processing single task object');
        this.processTaskData(data);
        return;
      }

      // 通用状态消息处理
      this.notifyListeners('system_status', data);
      this.notifyListeners('*', { type: 'system_status', data });

    } catch (error) {
      console.error('Error in handlePollingData:', error);
      console.error('Data that caused error:', data);
    }
  }

  private processTaskData(task: any): void {
    if (!task || typeof task !== 'object') {
      console.warn('Invalid task data:', task);
      return;
    }

    const message = {
      type: 'task_status_update',
      task_id: task.task_id || task.id || 'unknown',
      status: task.status || 'unknown',
      progress: Number(task.progress) || 0,
      downloaded_bytes: Number(task.downloaded_bytes) || 0,
      total_bytes: Number(task.total_bytes) || 0,
      download_speed: Number(task.download_speed) || 0,
      eta_seconds: Number(task.eta_seconds) || 0,
      error: task.error_message || task.error || null,
    };

    console.log('Processing task message:', message);

    this.notifyListeners('task_status_update', message);
    this.notifyListeners('download_progress', message);
    this.notifyListeners('*', { type: 'task_status_update', data: message });
  }

  private handlePollingError(): void {
    if (this.connectionState === 'connected' || this.connectionState === 'connecting') {
      this.connectionState = 'error';
      console.log("轮询连接状态更新为: error");

      // 通知状态变化
      this.notifyListeners('connection_status_changed', {
        state: 'error',
        mode: 'polling'
      });
    }
  }

  private notifyListeners(type: string, data: any): void {
    const callbacks = this.listeners.get(type);
    if (callbacks && callbacks.length > 0) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in communication callback for type ${type}:`, error);
        }
      });
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.options.maxReconnectAttempts})`);

      this.reconnectTimeoutId = window.setTimeout(() => {
        this.connect().catch(error => {
          console.error('Reconnection attempt failed:', error);
        });
      }, this.options.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached');
      this.connectionState = 'error';
    }
  }
}

// 导出单例获取器
export const getCommunicationService = (options?: CommunicationOptions) => {
  return CommunicationService.getInstance(options);
};