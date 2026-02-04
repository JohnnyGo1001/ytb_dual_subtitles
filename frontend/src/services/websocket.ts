/**
 * WebSocket Service for managing real-time communication
 * Handles download progress updates and system notifications
 */

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp?: string;
}

export interface DownloadProgressMessage {
  type: 'download_progress';
  data: {
    taskId: string;
    progress: number;
    status: 'pending' | 'downloading' | 'completed' | 'failed';
    filename?: string;
    fileSize?: number;
    downloadedSize?: number;
    speed?: string;
    eta?: string;
    error?: string;
  };
}

export interface SystemNotificationMessage {
  type: 'system_notification';
  data: {
    level: 'info' | 'warning' | 'error' | 'success';
    title: string;
    message: string;
  };
}

export type WebSocketMessageTypes = DownloadProgressMessage | SystemNotificationMessage;

export interface WebSocketServiceOptions {
  baseUrl?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export class WebSocketService {
  private static instance: WebSocketService | null = null;
  private ws: WebSocket | null = null;
  private url: string;
  private options: Required<WebSocketServiceOptions>;
  private listeners: Map<string, Array<(message: any) => void>> = new Map();
  private connectionState: 'connecting' | 'connected' | 'disconnected' | 'error' = 'disconnected';
  private reconnectAttempts = 0;
  private reconnectTimeoutId: number | null = null;
  private shouldReconnect = true;

  private constructor(options: WebSocketServiceOptions = {}) {
    const {
      baseUrl = 'ws://localhost:8000',
      reconnectInterval = 3000,
      maxReconnectAttempts = 5
    } = options;

    this.url = `${baseUrl}/ws`;
    this.options = { baseUrl, reconnectInterval, maxReconnectAttempts };
  }

  public static getInstance(options?: WebSocketServiceOptions): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService(options);
    }
    return WebSocketService.instance;
  }

  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.connectionState = 'connecting';
      this.shouldReconnect = true;

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          this.connectionState = 'connected';
          this.reconnectAttempts = 0;
          console.log('WebSocket connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onclose = () => {
          this.connectionState = 'disconnected';
          console.log('WebSocket disconnected');
          if (this.shouldReconnect) {
            this.handleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          this.connectionState = 'error';
          console.error('WebSocket error:', error);
          reject(new Error('WebSocket connection failed'));
        };

      } catch (error) {
        this.connectionState = 'error';
        reject(error);
      }
    });
  }

  public disconnect(): void {
    this.shouldReconnect = false;

    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.connectionState = 'disconnected';
  }

  public subscribe(messageType: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(messageType)) {
      this.listeners.set(messageType, []);
    }

    this.listeners.get(messageType)!.push(callback);

    // Return unsubscribe function
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

  public send(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        ...message,
        timestamp: new Date().toISOString()
      }));
    } else {
      console.warn('WebSocket is not connected, cannot send message');
    }
  }

  public getConnectionState(): string {
    return this.connectionState;
  }

  public isConnected(): boolean {
    return this.connectionState === 'connected' && this.ws?.readyState === WebSocket.OPEN;
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      const { type, data } = message;

      // Notify all listeners for this message type
      const callbacks = this.listeners.get(type);
      if (callbacks && callbacks.length > 0) {
        callbacks.forEach(callback => {
          try {
            callback(data);
          } catch (error) {
            console.error(`Error in WebSocket callback for type ${type}:`, error);
          }
        });
      }

      // Also notify global listeners
      const globalCallbacks = this.listeners.get('*');
      if (globalCallbacks && globalCallbacks.length > 0) {
        globalCallbacks.forEach(callback => {
          try {
            callback(message);
          } catch (error) {
            console.error('Error in global WebSocket callback:', error);
          }
        });
      }

    } catch (error) {
      console.error('Failed to parse WebSocket message:', event.data, error);
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

// Export singleton instance getter
export const getWebSocketService = (options?: WebSocketServiceOptions) => {
  return WebSocketService.getInstance(options);
};