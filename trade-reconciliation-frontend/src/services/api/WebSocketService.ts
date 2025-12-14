/**
 * WebSocketService provides functionality for WebSocket connections
 * with automatic reconnection and message handling.
 */

export interface WebSocketOptions {
  reconnectAttempts?: number;
  reconnectDelay?: number;
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
}

export class WebSocketService {
  private socket: WebSocket | null = null;
  private url: string;
  private options: WebSocketOptions;
  private reconnectAttempt = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private messageHandlers: Map<string, ((data: any) => void)[]> = new Map();

  constructor(url: string, options: WebSocketOptions = {}) {
    this.url = url;
    this.options = {
      reconnectAttempts: 5,
      reconnectDelay: 1000,
      ...options,
    };
  }

  /**
   * Connects to the WebSocket server
   */
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.socket = new WebSocket(this.url);

        this.socket.onopen = (event) => {
          console.log('WebSocket connected:', this.url);
          this.reconnectAttempt = 0;
          if (this.options.onOpen) {
            this.options.onOpen(event);
          }
          resolve();
        };

        this.socket.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          if (this.options.onClose) {
            this.options.onClose(event);
          }
          this.attemptReconnect();
        };

        this.socket.onerror = (event) => {
          console.error('WebSocket error:', event);
          if (this.options.onError) {
            this.options.onError(event);
          }
          reject(event);
        };

        this.socket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            const { type, data } = message;
            
            if (type && this.messageHandlers.has(type)) {
              const handlers = this.messageHandlers.get(type) || [];
              handlers.forEach(handler => handler(data));
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };
      } catch (error) {
        console.error('Error connecting to WebSocket:', error);
        reject(error);
        this.attemptReconnect();
      }
    });
  }

  /**
   * Disconnects from the WebSocket server
   */
  public disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  /**
   * Sends a message to the WebSocket server
   */
  public send(type: string, data: any): boolean {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ type, data });
      this.socket.send(message);
      return true;
    }
    return false;
  }

  /**
   * Adds a message handler for a specific message type
   */
  public on(type: string, handler: (data: any) => void): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    
    const handlers = this.messageHandlers.get(type)!;
    handlers.push(handler);
    
    // Return a function to remove this handler
    return () => {
      const index = handlers.indexOf(handler);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    };
  }

  /**
   * Attempts to reconnect to the WebSocket server
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempt >= (this.options.reconnectAttempts || 0)) {
      console.log('Maximum reconnect attempts reached');
      return;
    }
    
    this.reconnectAttempt++;
    const delay = this.options.reconnectDelay! * Math.pow(2, this.reconnectAttempt - 1);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempt})`);
    
    this.reconnectTimeout = setTimeout(() => {
      console.log(`Reconnecting... (attempt ${this.reconnectAttempt})`);
      this.connect().catch(() => {
        // Error handling is done in the connect method
      });
    }, delay);
  }

  /**
   * Checks if the WebSocket is connected
   */
  public isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}