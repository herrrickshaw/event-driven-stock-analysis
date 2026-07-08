import type { WebSocketMessage, PriceUpdate, AlertEvent } from '@types/index'

export enum WebSocketEventType {
  PRICE_UPDATE = 'price_update',
  KPI_UPDATE = 'kpi_update',
  ALERT = 'alert',
  REBALANCE_STATUS = 'rebalance_status',
  MARKET_DATA = 'market_data',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
}

type WebSocketEventHandler = (data: any) => void

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private heartbeatInterval: NodeJS.Timeout | null = null
  private listeners: Map<WebSocketEventType, Set<WebSocketEventHandler>> = new Map()

  constructor(url?: string) {
    this.url = url || `ws://${window.location.host}/ws`
  }

  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.reconnectAttempts = 0
          this.startHeartbeat()
          this.emit(WebSocketEventType.CONNECTED, { timestamp: new Date().toISOString() })
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(JSON.parse(event.data))
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.emit(WebSocketEventType.ERROR, error)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket disconnected')
          this.stopHeartbeat()
          this.emit(WebSocketEventType.DISCONNECTED, { timestamp: new Date().toISOString() })
          this.attemptReconnect()
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  public disconnect(): void {
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  public send(type: string, data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type,
          data,
          timestamp: new Date().toISOString(),
        })
      )
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  public subscribe(market: string, symbols?: string[]): void {
    this.send('subscribe', { market, symbols })
  }

  public unsubscribe(market: string, symbols?: string[]): void {
    this.send('unsubscribe', { market, symbols })
  }

  public on(eventType: WebSocketEventType, handler: WebSocketEventHandler): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set())
    }
    this.listeners.get(eventType)!.add(handler)

    // Return unsubscribe function
    return () => {
      this.listeners.get(eventType)?.delete(handler)
    }
  }

  public off(eventType: WebSocketEventType, handler: WebSocketEventHandler): void {
    this.listeners.get(eventType)?.delete(handler)
  }

  private emit(eventType: WebSocketEventType, data: any): void {
    const handlers = this.listeners.get(eventType)
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(data)
        } catch (error) {
          console.error(`Error in ${eventType} handler:`, error)
        }
      })
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    const { type, data } = message

    switch (type) {
      case 'price_update':
        this.emit(WebSocketEventType.PRICE_UPDATE, data as PriceUpdate)
        break
      case 'kpi_update':
        this.emit(WebSocketEventType.KPI_UPDATE, data)
        break
      case 'alert':
        this.emit(WebSocketEventType.ALERT, data as AlertEvent)
        break
      case 'rebalance_status':
        this.emit(WebSocketEventType.REBALANCE_STATUS, data)
        break
      case 'market_data':
        this.emit(WebSocketEventType.MARKET_DATA, data)
        break
      default:
        console.warn(`Unknown message type: ${type}`)
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      this.send('ping', { timestamp: new Date().toISOString() })
    }, 30000)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
      console.log(`Attempting to reconnect in ${delay}ms...`)
      setTimeout(() => this.connect().catch(console.error), delay)
    } else {
      console.error('Max reconnect attempts reached')
    }
  }

  public isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

// Singleton instance
let wsInstance: WebSocketClient | null = null

export function getWebSocketClient(): WebSocketClient {
  if (!wsInstance) {
    wsInstance = new WebSocketClient()
  }
  return wsInstance
}
