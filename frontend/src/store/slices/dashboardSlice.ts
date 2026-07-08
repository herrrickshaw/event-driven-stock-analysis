import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { DashboardState, PerformanceMetrics, RiskMetrics, MarketPerformance, KPIScorecard } from '@types/index'

const initialState: DashboardState = {
  portfolio: [],
  performance: {
    cagr: 0,
    sharpe_ratio: 0,
    ytd_return: 0,
    total_return: 0,
    start_date: '',
    end_date: '',
  },
  allocation: {
    by_market: {},
  },
  risk: {
    volatility: 0,
    var_95: 0,
    var_99: 0,
    max_drawdown: 0,
    sharpe_ratio: 0,
  },
  correlation: null,
  rebalancing: [],
  allocation_drift: [],
  market_performance: [],
  kpis: null,
  websocket_connected: false,
  loading: false,
  error: null,
  last_updated: '',
}

export const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    updatePerformance: (state, action: PayloadAction<PerformanceMetrics>) => {
      state.performance = action.payload
      state.last_updated = new Date().toISOString()
    },
    updateRisk: (state, action: PayloadAction<RiskMetrics>) => {
      state.risk = action.payload
      state.last_updated = new Date().toISOString()
    },
    updateAllocation: (state, action: PayloadAction<any>) => {
      state.allocation = action.payload
      state.last_updated = new Date().toISOString()
    },
    updateMarketPerformance: (state, action: PayloadAction<MarketPerformance[]>) => {
      state.market_performance = action.payload
      state.last_updated = new Date().toISOString()
    },
    updateKPIs: (state, action: PayloadAction<KPIScorecard>) => {
      state.kpis = action.payload
      state.last_updated = new Date().toISOString()
    },
    setWebSocketConnected: (state, action: PayloadAction<boolean>) => {
      state.websocket_connected = action.payload
    },
    resetDashboard: () => initialState,
  },
})

export const {
  setLoading,
  setError,
  updatePerformance,
  updateRisk,
  updateAllocation,
  updateMarketPerformance,
  updateKPIs,
  setWebSocketConnected,
  resetDashboard,
} = dashboardSlice.actions

export default dashboardSlice.reducer
