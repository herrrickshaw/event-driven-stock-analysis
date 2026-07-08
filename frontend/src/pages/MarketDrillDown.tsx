import React, { useEffect, useState } from 'react'
import { Card, KPICard } from '@components/cards'
import { LineChart, BarChart } from '@components/charts'
import { Table, Column } from '@components/tables'
import { Loading, Error } from '@components/common'
import { useAppDispatch, useAppSelector } from '@store/hooks'
import { updateMarketPerformance, setLoading, setError } from '@store/slices/dashboardSlice'
import apiService from '@services/api'
import type { Market, MarketPerformance } from '@types/index'

const MarketDrillDown: React.FC = () => {
  const dispatch = useAppDispatch()
  const { market_performance, loading, error } = useAppSelector((state) => state.dashboard)
  const [selectedMarket, setSelectedMarket] = useState<Market>('india')

  useEffect(() => {
    const fetchData = async () => {
      dispatch(setLoading(true))
      try {
        const data = await apiService.getMarketPerformance()
        dispatch(updateMarketPerformance(data))
      } catch (err) {
        dispatch(setError(err instanceof Error ? err.message : 'Failed to fetch market data'))
      } finally {
        dispatch(setLoading(false))
      }
    }

    fetchData()
  }, [dispatch])

  if (loading) return <Loading message="Loading market data..." />

  const currentMarket = market_performance.find((m) => m.market === selectedMarket) || market_performance[0]

  const performanceData = [
    { date: '2024-01', india: 100, us: 102, europe: 98, japan: 101, korea: 99 },
    { date: '2024-02', india: 105, us: 104, europe: 100, japan: 103, korea: 102 },
    { date: '2024-03', india: 102, us: 106, europe: 99, japan: 105, korea: 101 },
    { date: '2024-04', india: 110, us: 108, europe: 102, japan: 107, korea: 104 },
    { date: '2024-05', india: 115, us: 110, europe: 104, japan: 109, korea: 106 },
    { date: '2024-06', india: 118, us: 112, europe: 106, japan: 111, korea: 108 },
  ]

  const marketComparisonData = [
    { market: 'India', ytd: 8.5, allocation: 30 },
    { market: 'US', ytd: 12.3, allocation: 40 },
    { market: 'Europe', ytd: 5.2, allocation: 20 },
    { market: 'Japan', ytd: 3.1, allocation: 5 },
    { market: 'Korea', ytd: 6.8, allocation: 5 },
  ]

  const holdingsColumns: Column<any>[] = [
    { key: 'symbol', header: 'Symbol', sortable: true },
    { key: 'name', header: 'Company', sortable: true },
    { key: 'shares', header: 'Shares', sortable: true },
    { key: 'price', header: 'Price', render: (val) => `$${val.toFixed(2)}`, sortable: true },
    { key: 'change_pct', header: 'Change %', render: (val) => `${val > 0 ? '+' : ''}${val.toFixed(2)}%` },
    { key: 'allocation', header: 'Allocation', render: (val) => `${val.toFixed(2)}%` },
  ]

  const mockHoldings = [
    {
      symbol: 'RELIANCE',
      name: 'Reliance Industries',
      shares: 100,
      price: 2750.5,
      change_pct: 5.2,
      allocation: 25.3,
    },
    {
      symbol: 'TCS',
      name: 'Tata Consultancy Services',
      shares: 50,
      price: 3425.0,
      change_pct: 3.8,
      allocation: 18.2,
    },
    {
      symbol: 'INFY',
      name: 'Infosys Limited',
      shares: 75,
      price: 1525.25,
      change_pct: 2.1,
      allocation: 14.5,
    },
  ]

  return (
    <div className="space-y-6">
      {error && <Error message={error} />}

      {/* Market Selector */}
      <Card>
        <div className="flex gap-2 flex-wrap">
          {(['india', 'us', 'europe', 'japan', 'korea', 'uk', 'brazil', 'china'] as Market[]).map(
            (market) => (
              <button
                key={market}
                onClick={() => setSelectedMarket(market)}
                className={`px-4 py-2 rounded font-medium transition-colors ${
                  selectedMarket === market
                    ? 'bg-primary-600 text-white'
                    : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300'
                }`}
              >
                {market.toUpperCase()}
              </button>
            )
          )}
        </div>
      </Card>

      {/* Market KPIs */}
      {currentMarket && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            name="Current Value"
            value={currentMarket.current_value}
            unit="$"
            trend="up"
            change_pct={currentMarket.gain_loss_pct}
          />
          <KPICard
            name="Gain/Loss"
            value={currentMarket.gain_loss}
            unit="$"
            trend={currentMarket.gain_loss > 0 ? 'up' : 'down'}
            change_pct={currentMarket.gain_loss_pct}
          />
          <KPICard
            name="YTD Return"
            value={currentMarket.ytd_return}
            unit="%"
            trend="up"
            change_pct={2.5}
          />
          <KPICard
            name="Allocation"
            value={currentMarket.allocation_pct}
            unit="%"
            trend="neutral"
          />
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <LineChart
            data={performanceData}
            title={`${selectedMarket.toUpperCase()} Performance vs Peers`}
            lines={[
              { key: 'india', stroke: '#f59e0b', name: 'India' },
              { key: 'us', stroke: '#0ea5e9', name: 'US' },
              { key: 'europe', stroke: '#10b981', name: 'Europe' },
              { key: 'japan', stroke: '#8b5cf6', name: 'Japan' },
              { key: 'korea', stroke: '#ec4899', name: 'Korea' },
            ]}
            height={300}
          />
        </Card>
        <Card>
          <BarChart
            data={marketComparisonData}
            title="Market Performance Comparison"
            bars={[
              { key: 'ytd', fill: '#0ea5e9', name: 'YTD Return %' },
            ]}
            height={300}
          />
        </Card>
      </div>

      {/* Holdings Table */}
      <Card>
        <Table
          columns={holdingsColumns}
          data={mockHoldings}
          title={`Top Holdings - ${selectedMarket.toUpperCase()}`}
          sortable
        />
      </Card>

      {/* Market Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Market Stats" padding="sm">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Volatility</span>
              <span className="font-medium">14.2%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Sharpe</span>
              <span className="font-medium">1.25</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Sortino</span>
              <span className="font-medium">1.52</span>
            </div>
          </div>
        </Card>
        <Card title="Holdings" padding="sm">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Count</span>
              <span className="font-medium">45</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Avg Position</span>
              <span className="font-medium">2.2%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Top 10 Concentration</span>
              <span className="font-medium">45.3%</span>
            </div>
          </div>
        </Card>
        <Card title="Exposure" padding="sm">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Long</span>
              <span className="font-medium text-green-600">98.5%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Short</span>
              <span className="font-medium text-red-600">1.5%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">Cash</span>
              <span className="font-medium">0.0%</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

export default MarketDrillDown
