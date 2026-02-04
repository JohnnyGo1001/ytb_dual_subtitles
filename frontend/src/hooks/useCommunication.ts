import { useState, useRef, useEffect, useCallback } from 'react';
import { getCommunicationService, CommunicationOptions, CommunicationMode } from '@/services/communication';

export interface UseCommunicationOptions extends CommunicationOptions {
  onMessage?: (data: any) => void;
  onError?: (error: Event | Error) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoConnect?: boolean;
}

export interface UseCommunicationReturn {
  isConnected: boolean;
  error: string | null;
  mode: CommunicationMode;
  sendMessage: (data: any) => void;
  disconnect: () => void;
  connect: () => Promise<void>;
  subscribe: (messageType: string, callback: (data: any) => void) => () => void;
}

export function useCommunication(
  options: UseCommunicationOptions = {}
): UseCommunicationReturn {
  const {
    onMessage,
    onError,
    onConnect,
    onDisconnect,
    autoConnect = true,
    ...communicationOptions
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<CommunicationMode>('polling');

  const communicationService = useRef(getCommunicationService(communicationOptions));
  const subscriptions = useRef<Array<() => void>>([]);

  const connect = useCallback(async () => {
    try {
      setError(null);
      await communicationService.current.connect();

      // 连接完成后立即检查状态
      const connected = communicationService.current.isConnected();
      const currentMode = communicationService.current.getMode();

      console.log('Connect completed - connected:', connected, 'mode:', currentMode);

      setIsConnected(connected);
      setMode(currentMode);
      onConnect?.();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Connection failed';
      setError(errorMessage);
      setIsConnected(false);
      onError?.(err instanceof Error ? err : new Error(errorMessage));
    }
  }, [onConnect, onError]);

  const disconnect = useCallback(() => {
    communicationService.current.disconnect();
    setIsConnected(false);
    setMode('polling');
    onDisconnect?.();

    // 清理所有订阅
    subscriptions.current.forEach(unsubscribe => unsubscribe());
    subscriptions.current = [];
  }, [onDisconnect]);

  const sendMessage = useCallback((data: any) => {
    try {
      communicationService.current.send({
        type: 'message',
        data,
        timestamp: new Date().toISOString()
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      console.error('Failed to send message:', err);
    }
  }, []);

  const subscribe = useCallback((messageType: string, callback: (data: any) => void) => {
    const unsubscribe = communicationService.current.subscribe(messageType, callback);
    subscriptions.current.push(unsubscribe);
    return unsubscribe;
  }, []);

  useEffect(() => {
    // 初始化时立即检查一次状态
    const initialConnected = communicationService.current.isConnected();
    const initialMode = communicationService.current.getMode();

    console.log('Initial state check - connected:', initialConnected, 'mode:', initialMode);

    setIsConnected(initialConnected);
    setMode(initialMode);

    if (autoConnect) {
      connect();
    }

    // 订阅连接状态变化事件
    const connectionStatusUnsubscribe = communicationService.current.subscribe('connection_status_changed', (data: any) => {
      console.log('Connection status changed:', data);
      const connected = communicationService.current.isConnected();
      const currentMode = communicationService.current.getMode();

      setIsConnected(connected);
      setMode(currentMode);

      console.log('Updated hook state - connected:', connected, 'mode:', currentMode);
    });

    // 订阅所有其他消息
    const allMessagesUnsubscribe = communicationService.current.subscribe('*', (message: any) => {
      // 处理其他消息，但不重复处理连接状态
      if (message.type !== 'connection_status_changed') {
        // 传递消息给用户回调
        if (onMessage) {
          onMessage(message);
        }
      }
    });

    subscriptions.current.push(connectionStatusUnsubscribe);
    subscriptions.current.push(allMessagesUnsubscribe);

    // 定期检查连接状态
    const statusCheckInterval = setInterval(() => {
      const connected = communicationService.current.isConnected();
      const currentMode = communicationService.current.getMode();

      setIsConnected(connected);
      setMode(currentMode);

      // 如果连接断开且应该自动重连，尝试重连
      if (!connected && autoConnect) {
        connect().catch(err => {
          console.error('Auto-reconnect failed:', err);
        });
      }
    }, 5000);

    return () => {
      clearInterval(statusCheckInterval);
      disconnect();
    };
  }, [connect, disconnect, onMessage, autoConnect, mode]);

  return {
    isConnected,
    error,
    mode,
    sendMessage,
    disconnect,
    connect,
    subscribe,
  };
}