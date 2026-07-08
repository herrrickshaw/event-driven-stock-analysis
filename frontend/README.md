# Event-Driven Stock Dashboard

A comprehensive React-based dashboard for real-time event-driven stock portfolio analysis, risk management, and performance tracking. Built with React 18, TypeScript, Tailwind CSS, Redux, and Recharts.

## Overview

The dashboard provides institutional-grade portfolio analytics with 5 specialized views:

1. **Performance Summary** - CAGR, Sharpe Ratio, YTD return, current allocation
2. **Risk Dashboard** - Volatility, VaR (95%/99%), max drawdown, correlation matrix
3. **Rebalancing Calendar** - Scheduled dates, drift tracking, execution status
4. **Market Drill-Down** - Per-market performance (India/US/Europe/Japan/Korea/UK/Brazil/China)
5. **KPI Scorecard** - 15 daily KPIs with sparklines, trends, and alerts

## Tech Stack

- **Frontend Framework**: React 18.2+ with TypeScript
- **State Management**: Redux Toolkit + Redux Persist
- **Styling**: Tailwind CSS 3.3 with custom configuration
- **Charts**: Recharts 2.10+
- **Routing**: React Router 6.18+
- **API Client**: Axios with interceptors
- **Build Tool**: Vite 5.0+
- **Real-time**: WebSocket with automatic reconnection

## Project Structure

```
event-driven-stock-dashboard/
├── src/
│   ├── components/
│   │   ├── charts/
│   │   │   ├── LineChart.tsx      # Time series visualization
│   │   │   ├── BarChart.tsx       # Category comparison
│   │   │   ├── PieChart.tsx       # Distribution breakdown
│   │   │   ├── Sparkline.tsx      # Inline trend indicator
│   │   │   └── index.ts
│   │   ├── cards/
│   │   │   ├── Card.tsx           # Generic container card
│   │   │   ├── KPICard.tsx        # KPI display with alerts
│   │   │   └── index.ts
│   │   ├── tables/
│   │   │   ├── Table.tsx          # Sortable, paginated table
│   │   │   └── index.ts
│   │   └── common/
│   │       ├── Navigation.tsx     # Top nav bar with view tabs
│   │       ├── Loading.tsx        # Spinner + message
│   │       ├── Error.tsx          # Error message + retry
│   │       └── index.ts
│   ├── pages/
│   │   ├── PerformanceSummary.tsx # View 1: Portfolio metrics
│   │   ├── RiskDashboard.tsx      # View 2: Risk metrics
│   │   ├── RebalancingCalendar.tsx# View 3: Rebalancing
│   │   ├── MarketDrillDown.tsx    # View 4: Market breakdown
│   │   └── KPIScorecard.tsx       # View 5: Daily KPIs
│   ├── store/
│   │   ├── slices/
│   │   │   └── dashboardSlice.ts  # Redux dashboard state
│   │   ├── store.ts               # Redux store config
│   │   └── hooks.ts               # useAppDispatch, useAppSelector
│   ├── services/
│   │   ├── api.ts                 # Axios client + endpoints
│   │   └── websocket.ts           # WebSocket client + events
│   ├── types/
│   │   └── index.ts               # TypeScript interfaces
│   ├── App.tsx                    # Router setup + WebSocket init
│   ├── App.css                    # Global styles + animations
│   └── main.tsx                   # React entry point
├── public/                        # Static assets
├── index.html                     # HTML entry point
├── package.json                   # Dependencies + scripts
├── tsconfig.json                  # TypeScript config
├── tsconfig.node.json             # Vite TypeScript config
├── vite.config.ts                 # Vite build config
├── tailwind.config.js             # Tailwind theme + extends
├── postcss.config.js              # PostCSS + Tailwind plugin
├── .eslintrc.cjs                  # ESLint config
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

## Installation

### Prerequisites

- Node.js 16+ (v18+ recommended)
- npm or yarn
- Backend API running at `http://localhost:8000` (configurable in vite.config.ts)

### Setup

```bash
# Clone the project
cd event-driven-stock-dashboard

# Install dependencies
npm install

# Create .env file (optional, for custom API URLs)
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env.local
```

## Running the Development Server

```bash
# Start dev server (hot reload enabled)
npm run dev

# Server runs on http://localhost:5173
# Proxy: /api/* → http://localhost:8000/*
```

## Building for Production

```bash
# Type check
npm run type-check

# Build
npm run build

# Preview build locally
npm run preview

# Output: dist/
```

## Component Library

### Charts

All charts are responsive and support light/dark themes via CSS variables.

#### LineChart
```tsx
<LineChart
  data={timeSeriesData}
  title="Portfolio Performance"
  lines={[
    { key: 'value', stroke: '#0ea5e9', name: 'Portfolio' }
  ]}
  height={300}
  showLegend={true}
  showGrid={true}
/>
```

#### BarChart
```tsx
<BarChart
  data={categoryData}
  title="Monthly Returns"
  bars={[
    { key: 'return', fill: '#10b981', name: 'Return %' }
  ]}
  height={300}
  horizontal={false}
/>
```

#### PieChart
```tsx
<PieChart
  data={allocationData}
  title="Asset Allocation"
  colors={['#0ea5e9', '#10b981', '#f59e0b']}
  height={300}
/>
```

#### Sparkline
```tsx
<Sparkline
  data={[8, 10, 9, 11, 12]}
  color="#0ea5e9"
  trend="up"
  height={40}
/>
```

### Cards

#### Card (Generic Container)
```tsx
<Card
  title="My Card"
  subtitle="Subtitle"
  padding="md"
  bordered={true}
  action={<button>Action</button>}
>
  Content here
</Card>
```

#### KPICard (With Alert Support)
```tsx
<KPICard
  name="CAGR"
  value={12.5}
  unit="%"
  target={15}
  change_pct={2.3}
  trend="up"
  sparkline={[8, 10, 12]}
  alert={{
    type: 'warning',
    message: 'Below target'
  }}
/>
```

### Tables

```tsx
<Table
  columns={[
    { key: 'symbol', header: 'Symbol', sortable: true },
    { key: 'price', header: 'Price', render: (val) => `$${val}` }
  ]}
  data={holdings}
  title="Holdings"
  sortable={true}
  pageSize={10}
/>
```

## State Management (Redux)

### Dashboard Slice
Located in `src/store/slices/dashboardSlice.ts`:

```tsx
// State structure
{
  portfolio: PortfolioPosition[]
  performance: PerformanceMetrics
  allocation: CurrentAllocation
  risk: RiskMetrics
  correlation: CorrelationMatrix | null
  rebalancing: RebalancingSchedule[]
  allocation_drift: AllocationDrift[]
  market_performance: MarketPerformance[]
  kpis: KPIScorecard | null
  websocket_connected: boolean
  loading: boolean
  error: string | null
  last_updated: string
}

// Actions
updatePerformance(metrics)
updateRisk(metrics)
updateAllocation(allocation)
updateMarketPerformance(data)
updateKPIs(scorecard)
setWebSocketConnected(boolean)
setLoading(boolean)
setError(string | null)
```

### Using Redux Hooks

```tsx
import { useAppDispatch, useAppSelector } from '@store/hooks'
import { updatePerformance } from '@store/slices/dashboardSlice'

function MyComponent() {
  const dispatch = useAppDispatch()
  const { performance, loading } = useAppSelector(state => state.dashboard)

  useEffect(() => {
    dispatch(updatePerformance(newMetrics))
  }, [])

  return <>{/* JSX */}</>
}
```

## API Service

Centralized API client with error handling:

```tsx
import apiService from '@services/api'

// Performance endpoints
const metrics = await apiService.getPerformanceMetrics()
const historical = await apiService.getHistoricalPerformance('india')

// Risk endpoints
const risk = await apiService.getRiskMetrics()
const correlation = await apiService.getCorrelationMatrix()

// Rebalancing endpoints
const schedule = await apiService.getRebalancingSchedule()
const drift = await apiService.getAllocationDrift()

// Market endpoints
const performance = await apiService.getMarketPerformance('us')
const topHoldings = await apiService.getTopHoldings('india', 10)

// KPI endpoints
const scorecard = await apiService.getKPIScorecard()
const history = await apiService.getKPIHistory('kpi-id', 30)
```

## WebSocket Integration

Real-time event streaming with automatic reconnection:

```tsx
import { getWebSocketClient, WebSocketEventType } from '@services/websocket'

const ws = getWebSocketClient()

// Connect
await ws.connect()

// Subscribe to markets
ws.subscribe('india', ['NIFTY50', 'NIFTY500'])
ws.subscribe('us')

// Listen to events
ws.on(WebSocketEventType.PRICE_UPDATE, (priceData) => {
  console.log('Price updated:', priceData)
})

ws.on(WebSocketEventType.KPI_UPDATE, (kpiData) => {
  console.log('KPI updated:', kpiData)
})

ws.on(WebSocketEventType.ALERT, (alertData) => {
  console.log('Alert:', alertData)
})

// Unsubscribe
ws.unsubscribe('india', ['NIFTY50'])

// Disconnect
ws.disconnect()
```

## TypeScript Types

All types defined in `src/types/index.ts`:

```tsx
// Portfolio
PortfolioPosition
PerformanceMetrics
CurrentAllocation

// Risk
RiskMetrics
CorrelationMatrix

// Rebalancing
RebalancingSchedule
AllocationDrift

// Markets
Market ('india' | 'us' | 'europe' | 'japan' | 'korea' | 'uk' | 'brazil' | 'china')
MarketPerformance
MarketHolding

// KPIs
KPI
KPIScorecard

// WebSocket
WebSocketMessage
PriceUpdate
AlertEvent

// API
ApiResponse<T>
DashboardState
```

## Styling

### Tailwind Configuration

Located in `tailwind.config.js` with:
- Custom color palette (primary, success, warning, danger, neutral)
- Extended spacing scale (xs, sm, md, lg, xl, 2xl)
- Custom shadows (card, card-lg)
- Built-in dark mode support

### Dark Mode

Components automatically support both light and dark themes via:
1. System preference detection (`prefers-color-scheme: dark`)
2. Tailwind dark mode class (`dark:` utilities)

```tsx
// Example
<div className="bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100">
```

### CSS Classes

- `.glass-effect` - Glassmorphism backdrop blur
- `.transition-all` - Smooth transitions
- `.animate-fade-in` - Fade animation
- `.animate-slide-in-up` - Slide up animation

## Views

### 1. Performance Summary
- Portfolio CAGR, Sharpe Ratio, YTD return
- Interactive performance chart
- Current allocation pie chart
- Top holdings table with sortable columns
- Real-time position updates via WebSocket

### 2. Risk Dashboard
- Volatility, VaR (95%/99%), max drawdown KPIs
- Monthly volatility bar chart
- Maximum drawdown line chart
- Asset correlation matrix table
- Sharpe, Sortino, Calmar ratios

### 3. Rebalancing Calendar
- Days until next rebalance
- Max drift across markets
- Number of drifted markets
- YTD rebalance count
- Allocation drift alert panel
- Current drift tracking table
- Scheduled rebalancing calendar
- Rebalancing rules configuration

### 4. Market Drill-Down
- Market selector buttons (8 markets)
- Per-market KPIs (value, gain/loss, YTD return, allocation)
- Multi-market performance comparison chart
- Market comparison bar chart
- Top holdings table for selected market
- Market statistics (volatility, Sharpe, concentration)

### 5. KPI Scorecard
- Overall health score (0-100)
- Warning and critical alert counts
- 15 daily KPIs with sparklines
- KPI name, value, unit, target, trend, alerts
- Sortable/paginated KPI detail table
- Active alerts panel with severity levels

## Key Features

✅ **5 Specialized Views** - Tailored analytics for different portfolio aspects
✅ **Real-time WebSocket** - Live price, KPI, and alert streaming
✅ **Responsive Design** - Mobile, tablet, desktop optimized
✅ **Dark Mode** - Full light/dark theme support
✅ **Type Safety** - 100% TypeScript with strict mode
✅ **Component Library** - Reusable charts, cards, tables, common components
✅ **Centralized State** - Redux for predictable state management
✅ **API Abstraction** - Clean service layer with error handling
✅ **Accessibility** - Semantic HTML, ARIA labels where needed
✅ **Performance** - Code splitting, lazy loading, optimized re-renders

## Environment Variables

Create `.env.local`:

```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws
```

If not set, defaults to:
- API: `http://localhost:8000/api`
- WebSocket: `ws://localhost:8000/ws`

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Android)

## Performance Optimization

- Memoized components with React.memo
- Lazy loading with React.lazy + Suspense
- Code splitting by route
- Virtualized tables for large datasets (ready to implement)
- Debounced API calls
- Redux selector memoization

## Development Workflow

### TypeScript

```bash
# Type checking
npm run type-check

# Watch mode
npx tsc --watch
```

### ESLint

```bash
# Lint
npm run lint

# Fix auto-fixable issues
npx eslint src --fix
```

### Hot Module Replacement

Vite provides HMR out of the box. Changes to React components automatically reflect without full page reload.

## API Endpoints Expected

The dashboard expects a backend API with these endpoints:

```
GET  /api/performance/metrics       → PerformanceMetrics
GET  /api/performance/historical    → TimeSeriesData[]
GET  /api/risk/metrics              → RiskMetrics
GET  /api/risk/correlation          → CorrelationMatrix
GET  /api/risk/var                  → VaRData
GET  /api/rebalancing/schedule      → RebalancingSchedule[]
GET  /api/rebalancing/drift         → AllocationDrift[]
POST /api/rebalancing/{id}/execute  → ExecutionResult
GET  /api/markets/performance       → MarketPerformance[]
GET  /api/markets/{market}/details  → MarketDetails
GET  /api/markets/{market}/holdings → MarketHolding[]
GET  /api/kpis/scorecard            → KPIScorecard
GET  /api/kpis/{id}/history         → TimeSeriesData[]
GET  /api/portfolio/summary         → PortfolioData
GET  /api/portfolio/positions       → PortfolioPosition[]
GET  /api/alerts                    → AlertEvent[]
POST /api/alerts/{id}/dismiss       → void
GET  /api/health                    → { status: 'ok' }

WS   /ws                            → WebSocket for real-time updates
```

## Extending the Dashboard

### Adding a New Page

1. Create `src/pages/MyView.tsx`
2. Import necessary components and hooks
3. Add Redux integration as needed
4. Add route in `src/App.tsx`
5. Update navigation in `src/components/common/Navigation.tsx`

### Adding a New Chart Type

1. Create `src/components/charts/MyChart.tsx`
2. Use Recharts as base
3. Implement custom tooltip
4. Export from `src/components/charts/index.ts`

### Adding Redux Slice

1. Create slice in `src/store/slices/mySlice.ts`
2. Import and add to store in `src/store/store.ts`
3. Use `useAppDispatch` and `useAppSelector` hooks

## Deployment

### Vercel/Netlify

```bash
npm run build
# Deploy dist/ folder
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY . .
RUN npm install && npm run build
EXPOSE 5173
CMD ["npm", "run", "preview"]
```

## Troubleshooting

### WebSocket Connection Fails
- Ensure backend WebSocket server is running
- Check CORS headers if on different domain
- Verify firewall/proxy settings

### API Calls Return 404
- Verify backend API is running on configured URL
- Check API endpoint paths
- Ensure CORS headers allow requests

### Styles Not Applied
- Clear node_modules: `rm -rf node_modules && npm install`
- Rebuild Tailwind: `npm run build`
- Check dark mode class on root element

### Performance Issues
- Use React DevTools Profiler
- Check Network tab for API waterfall
- Verify Redux action batching
- Profile WebSocket message frequency

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or feature requests, please open an issue in the repository.

---

**Built with ♥ for institutional portfolio analytics**
