# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
cd event-driven-stock-dashboard
npm install
```

### 2. Configure API URL (Optional)

Create `.env.local`:

```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws
```

Defaults to `http://localhost:8000/api` if not set.

### 3. Start Development Server

```bash
npm run dev
```

Open http://localhost:5173

## Features

### Performance Summary View
- Portfolio metrics (CAGR, Sharpe, YTD return)
- Performance chart over time
- Current allocation pie chart
- Top holdings table

**Access:** http://localhost:5173/

### Risk Dashboard View
- Volatility, VaR (95%/99%), max drawdown
- Monthly volatility chart
- Maximum drawdown tracking
- Correlation matrix

**Access:** http://localhost:5173/risk

### Rebalancing Calendar View
- Days until next rebalance
- Allocation drift tracking
- Rebalancing schedule
- Alert panel for drift violations

**Access:** http://localhost:5173/rebalancing

### Market Drill-Down View
- 8 market selector buttons
- Per-market performance metrics
- Multi-market comparison chart
- Top holdings by market

**Access:** http://localhost:5173/markets

### KPI Scorecard View
- Overall health score (0-100)
- 15 daily KPIs with sparklines
- Alert management
- KPI trends and targets

**Access:** http://localhost:5173/kpis

## Component Examples

### Using Charts

```tsx
import { LineChart, BarChart, PieChart } from '@components/charts'

// Time series chart
<LineChart
  data={[{ date: '2024-01', value: 100 }, ...]}
  title="Performance"
  lines={[{ key: 'value', stroke: '#0ea5e9', name: 'Value' }]}
/>

// Category chart
<BarChart
  data={[{ market: 'India', ytd: 8.5 }, ...]}
  bars={[{ key: 'ytd', fill: '#0ea5e9' }]}
/>

// Allocation chart
<PieChart
  data={[{ name: 'India', value: 30, percentage: 30 }, ...]}
  colors={['#0ea5e9', '#10b981', '#f59e0b']}
/>
```

### Using Cards

```tsx
import { Card, KPICard } from '@components/cards'

// Generic card
<Card title="My Card" padding="md">
  Content here
</Card>

// KPI card with alert
<KPICard
  name="CAGR"
  value={12.5}
  unit="%"
  target={15}
  change_pct={2.3}
  trend="up"
  sparkline={[8, 10, 12]}
  alert={{ type: 'warning', message: 'Below target' }}
/>
```

### Using Tables

```tsx
import { Table } from '@components/tables'

<Table
  columns={[
    { key: 'symbol', header: 'Symbol', sortable: true },
    { key: 'price', header: 'Price', render: (val) => `$${val}` }
  ]}
  data={holdings}
  title="Holdings"
  sortable
  pageSize={10}
/>
```

### Using Redux

```tsx
import { useAppDispatch, useAppSelector } from '@store/hooks'
import { updatePerformance } from '@store/slices/dashboardSlice'

function MyComponent() {
  const dispatch = useAppDispatch()
  const performance = useAppSelector(state => state.dashboard.performance)

  useEffect(() => {
    apiService.getPerformanceMetrics().then(metrics => {
      dispatch(updatePerformance(metrics))
    })
  }, [dispatch])

  return <div>{performance.cagr}%</div>
}
```

### Using API Service

```tsx
import apiService from '@services/api'

// Fetch performance
const metrics = await apiService.getPerformanceMetrics()

// Fetch risk
const risk = await apiService.getRiskMetrics()

// Fetch market performance
const markets = await apiService.getMarketPerformance('india')

// Fetch KPIs
const scorecard = await apiService.getKPIScorecard()

// Get alerts
const alerts = await apiService.getAlerts(10)
```

### Using WebSocket

```tsx
import { getWebSocketClient, WebSocketEventType } from '@services/websocket'

const ws = getWebSocketClient()

// Connect
await ws.connect()

// Subscribe to markets
ws.subscribe('india', ['NIFTY50', 'NIFTY500'])

// Listen to price updates
ws.on(WebSocketEventType.PRICE_UPDATE, (data) => {
  console.log('Price:', data.symbol, data.price)
})

// Listen to KPI updates
ws.on(WebSocketEventType.KPI_UPDATE, (data) => {
  console.log('KPI:', data.kpi_id, data.value)
})

// Listen to alerts
ws.on(WebSocketEventType.ALERT, (data) => {
  console.log('Alert:', data.message)
})

// Disconnect
ws.disconnect()
```

## Build for Production

```bash
# Type check
npm run type-check

# Build
npm run build

# Preview
npm run preview

# Output: dist/ (ready to deploy)
```

## Project Structure

```
src/
├── components/
│   ├── charts/         # LineChart, BarChart, PieChart, Sparkline
│   ├── cards/          # Card, KPICard
│   ├── tables/         # Table with sorting/pagination
│   └── common/         # Navigation, Loading, Error
├── pages/              # 5 main views
├── store/              # Redux setup
├── services/           # API + WebSocket
├── types/              # TypeScript interfaces
└── App.tsx             # Router setup
```

## API Mock Data

Each page component includes mock data for development:

```tsx
// PerformanceSummary.tsx
const performanceChartData = [
  { date: '2024-01', value: 100 },
  { date: '2024-02', value: 105 },
  ...
]

// RiskDashboard.tsx
const volatilityData = [
  { month: 'Jan', volatility: 12.5 },
  ...
]

// Tables use mock data too
const mockKPIs = [...]
```

Comment out `apiService.fetch*()` calls to use mock data offline.

## Debugging

### Redux DevTools

Install [Redux DevTools Extension](https://github.com/reduxjs/redux-devtools-extension) for browser.

Then inspect state in DevTools:

```tsx
// See store.ts for middleware setup
```

### Network Debugging

Open browser DevTools → Network tab to inspect API calls.

### WebSocket Debugging

```tsx
const ws = getWebSocketClient()

// Add debug logging
ws.on(WebSocketEventType.PRICE_UPDATE, (data) => {
  console.log('WS Price:', data)
})
```

## Customization

### Change API URL

```env
REACT_APP_API_URL=https://your-api.com/api
```

### Add Dark Mode Toggle

In `Navigation.tsx`:

```tsx
const [darkMode, setDarkMode] = useState(false)

<button onClick={() => setDarkMode(!darkMode)}>
  {darkMode ? '🌙' : '☀️'}
</button>
```

### Customize Colors

Edit `tailwind.config.js`:

```js
colors: {
  primary: { 500: '#your-color' }
}
```

### Add New View

1. Create `src/pages/MyView.tsx`
2. Add route in `src/App.tsx`
3. Add tab in `src/components/common/Navigation.tsx`

### Add New Chart

1. Create `src/components/charts/MyChart.tsx`
2. Export from `src/components/charts/index.ts`
3. Use in pages

## Troubleshooting

### WebSocket Connection Fails
- Check backend is running: `curl http://localhost:8000/health`
- Verify firewall allows WebSocket
- Check browser console for errors

### API Returns 404
- Verify API base URL: `REACT_APP_API_URL`
- Check endpoint paths in `src/services/api.ts`
- Ensure backend implements all endpoints

### Styles Not Applied
- Clear cache: `npm cache clean --force`
- Reinstall: `rm -rf node_modules && npm install`
- Rebuild: `npm run build`

### Performance Issues
- Profile with React DevTools
- Check Network waterfall
- Verify WebSocket message frequency (should be < 1000/min)

## Common Tasks

### Update Mock Data

Edit in page components:

```tsx
const mockHoldings = [
  { symbol: 'AAPL', price: 150.5, ... }
]
```

### Add New KPI

In `KPIScorecard.tsx`:

```tsx
{
  id: 'new-kpi',
  name: 'New KPI',
  value: 42,
  unit: '%',
  trend: 'up',
  sparkline: [...]
}
```

### Change Theme Colors

Edit `tailwind.config.js` and update component classes:

```tsx
<div className="bg-primary-600 dark:bg-primary-800">
```

### Add Alert

In `RiskDashboard.tsx`:

```tsx
<KPICard
  alert={{
    type: 'critical',
    message: 'VaR 99% exceeded'
  }}
/>
```

## Next Steps

1. Connect to your backend API
2. Implement missing endpoints from `docs/API.md`
3. Set up WebSocket connection
4. Customize colors and branding
5. Add your portfolio data
6. Deploy to production

## Support

- Docs: `README.md`, `ARCHITECTURE.md`, `docs/API.md`
- Code Examples: See `src/pages/` for complete examples
- Issues: Check console for errors

---

**Happy coding! 🚀**
