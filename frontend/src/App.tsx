import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Navigation } from '@components/common'
import PerformanceSummary from '@pages/PerformanceSummary'
import RiskDashboard from '@pages/RiskDashboard'
import RebalancingCalendar from '@pages/RebalancingCalendar'
import MarketDrillDown from '@pages/MarketDrillDown'
import KPIScorecard from '@pages/KPIScorecard'
import { useAppDispatch } from '@store/hooks'
import { setWebSocketConnected } from '@store/slices/dashboardSlice'
import { getWebSocketClient, WebSocketEventType } from '@services/websocket'
import './App.css'

function App() {
  const dispatch = useAppDispatch()

  useEffect(() => {
    // Initialize WebSocket connection
    const ws = getWebSocketClient()

    const connectWebSocket = async () => {
      try {
        await ws.connect()
        dispatch(setWebSocketConnected(true))

        // Subscribe to relevant market data
        ws.subscribe('india', ['NIFTY50', 'NIFTY500'])
        ws.subscribe('us', ['SPY', 'QQQ', 'IWM'])

        // Listen to events
        ws.on(WebSocketEventType.PRICE_UPDATE, (data) => {
          console.log('Price update:', data)
        })

        ws.on(WebSocketEventType.KPI_UPDATE, (data) => {
          console.log('KPI update:', data)
        })

        ws.on(WebSocketEventType.ALERT, (data) => {
          console.log('Alert:', data)
        })

        ws.on(WebSocketEventType.DISCONNECTED, () => {
          dispatch(setWebSocketConnected(false))
        })

        ws.on(WebSocketEventType.CONNECTED, () => {
          dispatch(setWebSocketConnected(true))
        })
      } catch (error) {
        console.error('Failed to connect WebSocket:', error)
        dispatch(setWebSocketConnected(false))

        // Retry after delay
        setTimeout(connectWebSocket, 5000)
      }
    }

    connectWebSocket()

    // Cleanup
    return () => {
      ws.disconnect()
    }
  }, [dispatch])

  return (
    <Router>
      <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900">
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<PerformanceSummary />} />
            <Route path="/risk" element={<RiskDashboard />} />
            <Route path="/rebalancing" element={<RebalancingCalendar />} />
            <Route path="/markets" element={<MarketDrillDown />} />
            <Route path="/kpis" element={<KPIScorecard />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
