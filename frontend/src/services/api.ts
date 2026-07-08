import axios from 'axios'
import type {
  PerformanceMetrics,
  RiskMetrics,
  MarketPerformance,
  KPIScorecard,
  ApiResponse,
} from '@types/index'

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api'

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const apiService = {
  // Performance endpoints
  async getPerformanceMetrics(): Promise<PerformanceMetrics> {
    const response = await client.get<ApiResponse<PerformanceMetrics>>('/performance/metrics')
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch performance metrics')
    }
    return response.data.data!
  },

  async getHistoricalPerformance(marketFilter?: string) {
    const params = marketFilter ? { market: marketFilter } : {}
    const response = await client.get('/performance/historical', { params })
    return response.data.data
  },

  // Risk endpoints
  async getRiskMetrics(): Promise<RiskMetrics> {
    const response = await client.get<ApiResponse<RiskMetrics>>('/risk/metrics')
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch risk metrics')
    }
    return response.data.data!
  },

  async getCorrelationMatrix() {
    const response = await client.get('/risk/correlation')
    return response.data.data
  },

  async getValueAtRisk() {
    const response = await client.get('/risk/var')
    return response.data.data
  },

  // Rebalancing endpoints
  async getRebalancingSchedule() {
    const response = await client.get('/rebalancing/schedule')
    return response.data.data
  },

  async getAllocationDrift() {
    const response = await client.get('/rebalancing/drift')
    return response.data.data
  },

  async triggerRebalance(scheduleId: string) {
    const response = await client.post(`/rebalancing/${scheduleId}/execute`)
    return response.data.data
  },

  // Market drill-down endpoints
  async getMarketPerformance(market?: string) {
    const params = market ? { market } : {}
    const response = await client.get<ApiResponse<MarketPerformance[]>>('/markets/performance', {
      params,
    })
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch market performance')
    }
    return response.data.data!
  },

  async getMarketDetails(market: string) {
    const response = await client.get(`/markets/${market}/details`)
    return response.data.data
  },

  async getTopHoldings(market: string, limit = 10) {
    const response = await client.get(`/markets/${market}/holdings`, {
      params: { limit },
    })
    return response.data.data
  },

  // KPI endpoints
  async getKPIScorecard(): Promise<KPIScorecard> {
    const response = await client.get<ApiResponse<KPIScorecard>>('/kpis/scorecard')
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to fetch KPI scorecard')
    }
    return response.data.data!
  },

  async getKPIHistory(kpiId: string, days = 30) {
    const response = await client.get(`/kpis/${kpiId}/history`, {
      params: { days },
    })
    return response.data.data
  },

  // Portfolio endpoints
  async getPortfolioSummary() {
    const response = await client.get('/portfolio/summary')
    return response.data.data
  },

  async getPortfolioPositions() {
    const response = await client.get('/portfolio/positions')
    return response.data.data
  },

  // Alerts endpoints
  async getAlerts(limit = 10) {
    const response = await client.get('/alerts', { params: { limit } })
    return response.data.data
  },

  async dismissAlert(alertId: string) {
    const response = await client.post(`/alerts/${alertId}/dismiss`)
    return response.data.data
  },

  // Health check
  async healthCheck() {
    const response = await client.get('/health')
    return response.status === 200
  },
}

export default apiService
