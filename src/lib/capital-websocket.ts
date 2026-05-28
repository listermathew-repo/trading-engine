/**
 * Capital.com WebSocket Client
 * Streams real-time price updates for monitored instruments
 */

interface PriceUpdate {
  epic: string;
  bid: number;
  ask: number;
  timestamp: number;
}

interface CapitalSession {
  cst: string;
  securityToken: string;
  apiKey: string;
}

class CapitalWebSocketClient {
  private ws: WebSocket | null = null;
  private session: CapitalSession | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private priceCallbacks: Map<string, (update: PriceUpdate) => void> = new Map();
  private apiKey: string;
  private email: string;
  private password: string;

  constructor(apiKey: string, email: string, password: string) {
    this.apiKey = apiKey;
    this.email = email;
    this.password = password;
  }

  /**
   * Authenticate with Capital.com REST API to get session tokens
   */
  async authenticate(): Promise<boolean> {
    try {
      const response = await fetch(
        'https://api-capital.backend-capital.com/api/v1/session',
        {
          method: 'POST',
          headers: {
            'X-CAP-API-KEY': this.apiKey,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            identifier: this.email,
            password: this.password,
          }),
        }
      );

      if (!response.ok) {
        console.error('Capital.com auth failed:', response.status);
        return false;
      }

      this.session = {
        cst: response.headers.get('CST') || '',
        securityToken: response.headers.get('X-SECURITY-TOKEN') || '',
        apiKey: this.apiKey,
      };

      console.log('✅ Capital.com authenticated');
      return true;
    } catch (error) {
      console.error('Capital.com auth error:', error);
      return false;
    }
  }

  /**
   * Connect to Capital.com WebSocket API
   */
  async connect(): Promise<boolean> {
    if (!this.session) {
      const authSuccess = await this.authenticate();
      if (!authSuccess) return false;
    }

    try {
      this.ws = new WebSocket('wss://stream-capital.backend-capital.com/connect');

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected to Capital.com');
        this.reconnectAttempts = 0;
        this.sendAuthMessage();
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event.data);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed, reconnecting...');
        this.attemptReconnect();
      };

      return true;
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.attemptReconnect();
      return false;
    }
  }

  private sendAuthMessage() {
    if (!this.ws || !this.session) return;

    const authMessage = {
      action: 'auth',
      cst: this.session.cst,
      'X-SECURITY-TOKEN': this.session.securityToken,
      'X-CAP-API-KEY': this.session.apiKey,
    };

    this.ws.send(JSON.stringify(authMessage));
  }

  /**
   * Subscribe to price updates for an instrument
   */
  subscribe(epic: string, callback: (update: PriceUpdate) => void) {
    this.priceCallbacks.set(epic, callback);

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          action: 'subscribe',
          epic: epic,
        })
      );
    }
  }

  private handleMessage(data: string) {
    try {
      const message = JSON.parse(data);

      if (message.action === 'price') {
        const update: PriceUpdate = {
          epic: message.epic,
          bid: message.bid,
          ask: message.ask,
          timestamp: Date.now(),
        };

        const callback = this.priceCallbacks.get(message.epic);
        if (callback) {
          callback(update);
        }
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      console.log(
        `Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
      );
      setTimeout(() => this.connect(), delay);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export { CapitalWebSocketClient };
export type { PriceUpdate };
