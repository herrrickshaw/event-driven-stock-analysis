// Portfolio & Performance Types
export interface PortfolioPosition {
  symbol: string;
  market: Market;
  shares: number;
  cost_basis: number;
  current_price: number;
  allocation: number; // percentage
}

export interface PerformanceMetrics {
  cagr: number; // %
  sharpe_ratio: number;
  ytd_return: number; // %
  total_return: number; // %
  start_date: string;
  end_date: string;
}

export interface CurrentAllocation {
  by_market: Record<Market, number>;
  by_sector?: Record<string, number>;
  by_cap?: Record<'large' | 'mid' | 'small', number>;
}

// Risk Types
export interface RiskMetrics {
  volatility: number; // annualized %
  var_95: number; // Value at Risk 95%
  var_99: number; // Value at Risk 99%
  max_drawdown: number; // %
  sharpe_ratio: number;
  sortino_ratio?: number;
  calmar_ratio?: number;
}

export interface CorrelationMatrix {
  markets: Market[];
  data: number[][];
  timestamp: string;
}

// Rebalancing Types
export interface RebalancingSchedule {
  id: string;
  scheduled_date: string;
  frequency: 'weekly' | 'monthly' | 'quarterly' | 'semi-annual' | 'annual';
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  target_allocation: Record<Market, number>;
  actual_allocation?: Record<Market, number>;
  drift_tolerance: number; // percentage
}

export interface AllocationDrift {
  market: Market;
  target: number;
  current: number;
  drift: number; // absolute percentage points
  threshold_exceeded: boolean;
}

// Market Types
export type Market = 'india' | 'us' | 'europe' | 'japan' | 'korea' | 'uk' | 'brazil' | 'china';

export interface MarketPerformance {
  market: Market;
  current_value: number;
  gain_loss: number;
  gain_loss_pct: number;
  ytd_return: number;
  allocation_pct: number;
  top_holdings: MarketHolding[];
}

export interface MarketHolding {
  symbol: string;
  name: string;
  shares: number;
  current_price: number;
  change_pct: number;
  allocation_pct: number;
}

// KPI Types
export interface KPI {
  id: string;
  name: string;
  value: number | string;
  unit: string;
  target?: number;
  change_pct?: number;
  trend?: 'up' | 'down' | 'neutral';
  sparkline?: number[];
  alert?: {
    type: 'warning' | 'critical' | 'info';
    message: string;
  };
}

export interface KPIScorecard {
  timestamp: string;
  kpis: KPI[];
  health_score: number; // 0-100
  alerts_count: number;
}

// WebSocket Event Types
export interface WebSocketMessage {
  type: 'price_update' | 'kpi_update' | 'alert' | 'rebalance_status' | 'market_data';
  timestamp: string;
  data: any;
}

export interface PriceUpdate {
  symbol: string;
  market: Market;
  price: number;
  change_pct: number;
  volume?: number;
  timestamp: string;
}

export interface AlertEvent {
  id: string;
  type: 'price_threshold' | 'allocation_drift' | 'portfolio_milestone' | 'rebalance_reminder';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  action_required: boolean;
  timestamp: string;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface DashboardState {
  portfolio: PortfolioPosition[];
  performance: PerformanceMetrics;
  allocation: CurrentAllocation;
  risk: RiskMetrics;
  correlation: CorrelationMatrix | null;
  rebalancing: RebalancingSchedule[];
  allocation_drift: AllocationDrift[];
  market_performance: MarketPerformance[];
  kpis: KPIScorecard | null;
  websocket_connected: boolean;
  loading: boolean;
  error: string | null;
  last_updated: string;
}

// Chart Data Types
export interface TimeSeriesData {
  date: string;
  value: number;
  [key: string]: string | number;
}

export interface DistributionData {
  name: string;
  value: number;
  percentage: number;
}
