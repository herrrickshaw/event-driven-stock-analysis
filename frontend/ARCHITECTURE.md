# Architecture & Design Decisions

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React App (5173)                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Navigation (View Selector)                           │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Route-based Pages                                  │    │
│  │  ├─ PerformanceSummary                              │    │
│  │  ├─ RiskDashboard                                   │    │
│  │  ├─ RebalancingCalendar                             │    │
│  │  ├─ MarketDrillDown                                 │    │
│  │  └─ KPIScorecard                                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                      ↓                                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Redux Store (Single Source of Truth)               │    │
│  │  ├─ dashboard (performance, risk, allocation, etc)  │    │
│  └─────────────────────────────────────────────────────┘    │
│                      ↓                                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Services Layer                                     │    │
│  │  ├─ apiService (REST calls)                         │    │
│  │  └─ WebSocketClient (real-time events)             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                      ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│          Backend API (FastAPI, 8000)                        │
│  ├─ /api/performance/*   (metrics, historical)              │
│  ├─ /api/risk/*          (volatility, VaR, correlation)     │
│  ├─ /api/rebalancing/*   (schedule, drift, execute)         │
│  ├─ /api/markets/*       (performance, holdings)            │
│  ├─ /api/kpis/*          (scorecard, history)               │
│  ├─ /api/portfolio/*     (summary, positions)               │
│  ├─ /api/alerts/*        (list, dismiss)                    │
│  ├─ /api/health          (status check)                     │
│  └─ /ws                  (WebSocket stream)                 │
│      └─ price_update, kpi_update, alert, etc                │
└─────────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  Data Layer (Cassandra, PostgreSQL, Cache)                  │
│  ├─ Portfolio positions (NSE/BSE/US/Europe/etc)             │
│  ├─ Price history & quotes                                  │
│  ├─ KPI timeseries                                          │
│  └─ Rebalancing records                                     │
└─────────────────────────────────────────────────────────────┘
```

## Component Hierarchy

```
App
├── Router
│   ├── Navigation
│   │   └── [View selector tabs]
│   │
│   └── Route Pages
│       ├── PerformanceSummary
│       │   ├── KPICard[] (CAGR, Sharpe, YTD, Total Return)
│       │   ├── LineChart (Performance over time)
│       │   ├── PieChart (Current Allocation)
│       │   └── Table (Holdings)
│       │
│       ├── RiskDashboard
│       │   ├── KPICard[] (Volatility, VaR95/99, MaxDD, Sharpe)
│       │   ├── BarChart (Monthly Volatility)
│       │   ├── LineChart (Drawdown)
│       │   └── Table (Correlation Matrix)
│       │
│       ├── RebalancingCalendar
│       │   ├── KPICard[] (Days to rebalance, Max drift, etc)
│       │   ├── Card (Alert Panel)
│       │   ├── Table (Drift Tracking)
│       │   ├── Table (Schedule)
│       │   └── Card (Rules Config)
│       │
│       ├── MarketDrillDown
│       │   ├── Card (Market Selector)
│       │   ├── KPICard[] (Per-market metrics)
│       │   ├── LineChart (Multi-market comparison)
│       │   ├── BarChart (Market performance)
│       │   ├── Table (Holdings)
│       │   └── Card[] (Market stats)
│       │
│       └── KPIScorecard
│           ├── Card[] (Health score, alerts)
│           ├── KPICard[] (15 KPIs)
│           ├── Table (KPI details)
│           └── Card (Active alerts)
```

## State Management (Redux)

### Dashboard Slice Structure

```
state.dashboard = {
  // Portfolio Data
  portfolio: PortfolioPosition[]
  
  // Performance Metrics
  performance: {
    cagr: number
    sharpe_ratio: number
    ytd_return: number
    total_return: number
    start_date: string
    end_date: string
  }
  
  // Current Allocation
  allocation: {
    by_market: Record<Market, number>
    by_sector?: Record<string, number>
    by_cap?: Record<'large' | 'mid' | 'small', number>
  }
  
  // Risk Metrics
  risk: {
    volatility: number
    var_95: number
    var_99: number
    max_drawdown: number
    sharpe_ratio: number
    sortino_ratio?: number
    calmar_ratio?: number
  }
  
  // Correlations
  correlation: CorrelationMatrix | null
  
  // Rebalancing
  rebalancing: RebalancingSchedule[]
  allocation_drift: AllocationDrift[]
  
  // Markets
  market_performance: MarketPerformance[]
  
  // KPIs
  kpis: KPIScorecard | null
  
  // UI State
  websocket_connected: boolean
  loading: boolean
  error: string | null
  last_updated: string
}
```

### Data Flow

```
Component
  ↓
useAppDispatch() → Action Creator
  ↓
Redux Reducer
  ↓
State Update → useAppSelector()
  ↓
Component Re-render
```

### Async Operations

```
Component (useEffect)
  ↓
dispatch(setLoading(true))
  ↓
apiService.fetch*()
  ↓
If Success:
  dispatch(update*()) → Redux
  ↓
If Error:
  dispatch(setError(message))
  ↓
dispatch(setLoading(false))
```

## Data Flow Patterns

### Real-Time Updates (WebSocket)

```
WebSocket Connection Established
  ↓
Subscribe to Markets
  ↓
Server sends Events:
  ├─ price_update → Update portfolio values
  ├─ kpi_update → Update KPI display
  ├─ alert → Show notification
  ├─ rebalance_status → Update progress
  └─ market_data → Update market performance
  ↓
Dispatch Redux Actions
  ↓
Components re-render with new data
```

### Polling Data (When WebSocket unavailable)

```
Component Mount
  ↓
setLoading(true)
  ↓
apiService.fetch*()
  ↓
Dispatch Redux Action
  ↓
dispatch(setLoading(false))
  ↓
Optional: useEffect cleanup/poll interval
```

## Component Design Principles

### 1. Presentational Components (Reusable)

Located in `src/components/`:

- **LineChart, BarChart, PieChart, Sparkline** - Chart components
  - Accept data array + configuration
  - Handle own styling + responsive behavior
  - Support light/dark themes
  
- **Card, KPICard** - Container components
  - Accept children or specific props
  - Consistent spacing + shadows
  - Optional header, action buttons
  
- **Table** - Data display component
  - Configurable columns
  - Built-in sorting + pagination
  - Responsive design

- **Loading, Error, Navigation** - Common UI components
  - Reused across pages
  - Handle error states gracefully

### 2. Container Components (Pages)

Located in `src/pages/`:

- Fetch data via Redux + API service
- Compose presentational components
- Handle loading/error states
- Own routing-specific logic

### 3. Service Layer

Located in `src/services/`:

- **api.ts** - Centralized REST API client
  - Request/response transformation
  - Error handling + retry logic
  - Type-safe endpoints
  
- **websocket.ts** - WebSocket connection management
  - Automatic reconnection
  - Event subscription/unsubscription
  - Connection state management

## Styling Architecture

### Tailwind CSS Strategy

- **Default (Light Mode)**: Base utilities
- **Dark Mode**: `dark:` prefixed utilities
- **Custom Classes**: CSS modules for complex animations
- **Component Library**: Consistent spacing scale (xs, sm, md, lg, xl)

### Color Palette

```
Primary (Blue):     #0ea5e9  (light: #38bdf8, dark: #075985)
Success (Green):    #10b981
Warning (Amber):    #f59e0b
Danger (Red):       #ef4444
Neutral (Gray):     #6b7280
```

### Spacing Scale

```
xs: 0.5rem
sm: 1rem
md: 1.5rem
lg: 2rem
xl: 3rem
2xl: 4rem
```

## Performance Optimization Strategies

### 1. Component Memoization

```tsx
const MemoizedChart = React.memo(LineChart, (prevProps, nextProps) => {
  return JSON.stringify(prevProps) === JSON.stringify(nextProps)
})
```

### 2. Lazy Loading

```tsx
const KPIScorecard = lazy(() => import('@pages/KPIScorecard'))

<Suspense fallback={<Loading />}>
  <KPIScorecard />
</Suspense>
```

### 3. Code Splitting by Route

Vite automatically splits by route entry points.

### 4. Redux Selector Memoization

```tsx
const selectPerformance = (state) => state.dashboard.performance
const memoizedSelector = useMemo(() => selectPerformance, [state])
```

### 5. Debounced API Calls

```tsx
const debouncedSearch = useMemo(
  () => debounce((query) => apiService.search(query), 300),
  []
)
```

### 6. Virtual Scrolling (for large tables)

Can be added via react-window when needed:

```tsx
<FixedSizeList
  height={600}
  itemCount={1000}
  itemSize={35}
>
  {Row}
</FixedSizeList>
```

## Error Handling Strategy

### API Errors

```
HTTP Request
  ↓
If 2xx:
  Parse response → Dispatch success action
  ↓
If 4xx/5xx:
  Log error → dispatch(setError(message))
  ↓
If Network:
  Retry with exponential backoff
  ↓
dispatch(setLoading(false))
```

### WebSocket Errors

```
Connection Error
  ↓
dispatch(setWebSocketConnected(false))
  ↓
Attempt Reconnect:
  Delay: 3s × 2^(attempts-1)
  Max attempts: 5
  ↓
On Success:
  dispatch(setWebSocketConnected(true))
  ↓
On Failure:
  Fallback to API polling
```

### Component Error Boundary

Add Error Boundary wrapper if needed:

```tsx
<ErrorBoundary fallback={<Error />}>
  <App />
</ErrorBoundary>
```

## Type Safety

### End-to-End Type Coverage

```
API Response (JSON)
  ↓
Type Definition (TypeScript interface)
  ↓
Redux Action Payload (same type)
  ↓
Component Props (derived from Redux state)
  ↓
Render (fully typed)
```

### Type Generation

For backend APIs, consider:

```bash
# Generate types from OpenAPI spec
npx openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-fetch \
  -o src/generated
```

## Testing Strategy

### Unit Tests (Vitest + React Testing Library)

```tsx
describe('KPICard', () => {
  it('displays value and unit', () => {
    render(<KPICard name="Test" value={100} unit="$" />)
    expect(screen.getByText('100')).toBeInTheDocument()
  })
})
```

### Integration Tests

```tsx
describe('PerformanceSummary page', () => {
  it('fetches and displays performance data', async () => {
    render(<PerformanceSummary />)
    await waitFor(() => {
      expect(screen.getByText(/CAGR/)).toBeInTheDocument()
    })
  })
})
```

### E2E Tests (Playwright/Cypress)

```js
test('user can navigate between views', async ({ page }) => {
  await page.goto('http://localhost:5173')
  await page.click('button:has-text("Risk")')
  await expect(page.locator('h1')).toContainText('Risk Dashboard')
})
```

## Deployment Architecture

### Development

```
npm run dev
→ Vite dev server :5173
→ HMR enabled
→ API proxy to :8000
```

### Production Build

```
npm run build
→ tsc check
→ Vite bundle (chunks auto-split by route)
→ Minify + optimize
→ dist/ folder ready for deployment
```

### Docker Deployment

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY . .
RUN npm ci && npm run build
EXPOSE 5173
CMD ["npm", "run", "preview"]
```

### Cloud Deployment

**Vercel:**
```bash
vercel deploy
# Auto-detects Vite setup
# Environment: REACT_APP_API_URL, REACT_APP_WS_URL
```

**Netlify:**
```bash
netlify deploy --prod --dir=dist
```

**AWS S3 + CloudFront:**
```bash
npm run build
aws s3 sync dist/ s3://bucket-name/
```

## Security Considerations

### Frontend Security

1. **XSS Prevention**
   - Sanitize user inputs
   - Use React's automatic escaping
   - Avoid `dangerouslySetInnerHTML`

2. **CSRF Protection**
   - Server should use CSRF tokens
   - Include in request headers

3. **Content Security Policy**
   - Add CSP headers in index.html meta tags
   - Restrict script sources

4. **Authentication**
   - Store tokens in secure httpOnly cookies
   - Or use IndexedDB with 1-hour TTL
   - Implement token refresh

### API Security

1. **Rate Limiting**
   - Server-side rate limiting
   - Client-side request queuing

2. **Input Validation**
   - Validate API responses
   - Use TypeScript strict mode

3. **HTTPS Only**
   - Enforce in production
   - Use WSS for WebSocket

## Monitoring & Observability

### Error Tracking

```tsx
import Sentry from '@sentry/react'

Sentry.init({
  dsn: process.env.REACT_APP_SENTRY_DSN,
  environment: process.env.REACT_APP_ENV,
})
```

### Performance Monitoring

```tsx
import { reportWebVitals } from 'web-vitals'

reportWebVitals((metric) => {
  console.log(metric)
  // Send to analytics service
})
```

### Analytics

```tsx
// Track view changes
useEffect(() => {
  gtag.pageview({
    page_path: location.pathname,
    page_title: document.title,
  })
}, [location])
```

## Future Enhancements

1. **Offline Mode** - Service Worker + local data sync
2. **Real-time Notifications** - Push notifications for alerts
3. **Advanced Charting** - TradingView lightweight charts
4. **Performance Profiling** - Interactive drill-down by date range
5. **Backtesting Engine** - Historical scenario analysis
6. **AI Insights** - ML-powered anomaly detection + predictions
7. **Mobile App** - React Native version for iOS/Android
8. **Collaborative Features** - Multi-user portfolios + shared views

---

**Last Updated:** 2024-07-08
**Version:** 1.0.0
