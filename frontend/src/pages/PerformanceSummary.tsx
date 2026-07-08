import React, { useEffect } from 'react'
import { Card, KPICard } from '@components/cards'
import { LineChart, PieChart } from '@components/charts'
import { Table, Column } from '@components/tables'
import { Loading, Error } from '@components/common'
import { useAppDispatch, useAppSelector } from '@store/hooks'
import { updatePerformance, updateAllocation, setLoading, setError } from '@store/slices/dashboardSlice'
import apiService from '@services/api'

const PerformanceSummary: React.FC = () => {
  const dispatch = useAppDispatch()
  const { performance, allocation, loading, error } = useAppSelector((state) => state.dashboard)

  useEffect(() => {
    const fetchData = async () => {
      dispatch(setLoading(true))
      try {
        const [perfData, allocData] = await Promise.all([
          apiService.getPerformanceMetrics(),
          apiService.getPortfolioSummary(),
        ])
        dispatch(updatePerformance(perfData))
        dispatch(updateAllocation(allocData))
      } catch (err) {
        dispatch(setError(err instanceof Error ? err.message : 'Failed to fetch data'))
      } finally {
        dispatch(setLoading(false))
      }
    }

    fetchData()
  }, [dispatch])

  if (loading) return <Loading message="Loading performance data..." />

  const performanceChartData = [
    { date: '2024-01', value: 100 },
    { date: '2024-02', value: 105 },
    { date: '2024-03', value: 102 },
    { date: '2024-04', value: 110 },
    { date: '2024-05', value: 115 },
    { date: '2024-06', value: 118 },
  ]

  const allocationData = Object.entries(allocation.by_market || {}).map(([market, value]) => ({
    name: market.toUpperCase(),
    value: value as number,
    percentage: value as number,
  }))

  const holdingsColumns: Column<any>[] = [
    { key: 'symbol', header: 'Symbol', width: 'w-20' },
    { key: 'market', header: 'Market', width: 'w-20' },
    { key: 'shares', header: 'Shares', sortable: true },
    {
      key: 'current_price',
      header: 'Current Price',
      render: (val) => `$${val.toFixed(2)}`,
      sortable: true,
    },
    {
      key: 'allocation',
      header: 'Allocation %',
      render: (val) => `${val.toFixed(2)}%`,
      sortable: true,
    },
  ]

  return (
    <div className="space-y-6">
      {error && <Error message={error} />}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          name="CAGR"
          value={performance.cagr}
          unit="%"
          trend="up"
          change_pct={2.5}
          sparkline={[8, 10, 9, 11, 12, 13]}
        />
        <KPICard
          name="Sharpe Ratio"
          value={performance.sharpe_ratio}
          unit=""
          trend="up"
          change_pct={1.2}
          sparkline={[0.8, 1.0, 0.95, 1.1, 1.2, 1.25]}
        />
        <KPICard
          name="YTD Return"
          value={performance.ytd_return}
          unit="%"
          trend="up"
          change_pct={5.3}
          sparkline={[2, 4, 3, 5, 7, 8]}
        />
        <KPICard
          name="Total Return"
          value={performance.total_return}
          unit="%"
          trend="up"
          change_pct={3.1}
          sparkline={[15, 20, 18, 22, 25, 28]}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <LineChart
            data={performanceChartData}
            title="Portfolio Performance"
            lines={[
              { key: 'value', stroke: '#0ea5e9', name: 'Portfolio Value' },
            ]}
            height={300}
          />
        </Card>
        <Card>
          <PieChart
            data={allocationData}
            title="Current Allocation"
            colors={['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']}
            height={300}
          />
        </Card>
      </div>

      {/* Holdings Table */}
      <Card>
        <Table
          columns={holdingsColumns}
          data={[
            {
              symbol: 'AAPL',
              market: 'us',
              shares: 100,
              current_price: 185.5,
              allocation: 25.3,
            },
            {
              symbol: 'RELIANCE',
              market: 'india',
              shares: 50,
              current_price: 2750.0,
              allocation: 18.2,
            },
            {
              symbol: 'ASML.AS',
              market: 'europe',
              shares: 75,
              current_price: 820.0,
              allocation: 22.1,
            },
          ]}
          title="Top Holdings"
          sortable
        />
      </Card>
    </div>
  )
}

export default PerformanceSummary
