import React, { useEffect } from 'react'
import { Card, KPICard } from '@components/cards'
import { BarChart, LineChart } from '@components/charts'
import { Table, Column } from '@components/tables'
import { Loading, Error } from '@components/common'
import { useAppDispatch, useAppSelector } from '@store/hooks'
import { updateRisk, setLoading, setError } from '@store/slices/dashboardSlice'
import apiService from '@services/api'

const RiskDashboard: React.FC = () => {
  const dispatch = useAppDispatch()
  const { risk, loading, error } = useAppSelector((state) => state.dashboard)

  useEffect(() => {
    const fetchData = async () => {
      dispatch(setLoading(true))
      try {
        const riskData = await apiService.getRiskMetrics()
        dispatch(updateRisk(riskData))
      } catch (err) {
        dispatch(setError(err instanceof Error ? err.message : 'Failed to fetch risk data'))
      } finally {
        dispatch(setLoading(false))
      }
    }

    fetchData()
  }, [dispatch])

  if (loading) return <Loading message="Loading risk metrics..." />

  const volatilityData = [
    { month: 'Jan', volatility: 12.5 },
    { month: 'Feb', volatility: 13.2 },
    { month: 'Mar', volatility: 11.8 },
    { month: 'Apr', volatility: 14.3 },
    { month: 'May', volatility: 13.5 },
    { month: 'Jun', volatility: 12.1 },
  ]

  const drawdownData = [
    { date: '2024-01-01', drawdown: 0 },
    { date: '2024-02-15', drawdown: -8.5 },
    { date: '2024-03-10', drawdown: -5.2 },
    { date: '2024-04-20', drawdown: -12.3 },
    { date: '2024-05-25', drawdown: -3.1 },
    { date: '2024-06-30', drawdown: -1.8 },
  ]

  const correlationColumns: Column<any>[] = [
    { key: 'asset', header: 'Asset Pair', width: 'w-32' },
    { key: 'correlation', header: 'Correlation', render: (val) => val.toFixed(3) },
    { key: 'change', header: 'Change', render: (val) => `${val > 0 ? '+' : ''}${val.toFixed(2)}` },
    { key: 'trend', header: 'Trend' },
  ]

  return (
    <div className="space-y-6">
      {error && <Error message={error} />}

      {/* Risk KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          name="Volatility (Annual)"
          value={risk.volatility}
          unit="%"
          trend="down"
          change_pct={-1.5}
          sparkline={[12, 13, 14, 12, 11, 12]}
        />
        <KPICard
          name="VaR 95%"
          value={risk.var_95}
          unit="$"
          target={-15000}
          sparkline={[12, 13, 14, 12, 11, 12]}
        />
        <KPICard
          name="VaR 99%"
          value={risk.var_99}
          unit="$"
          target={-22000}
          sparkline={[18, 20, 21, 19, 18, 17]}
        />
        <KPICard
          name="Max Drawdown"
          value={risk.max_drawdown}
          unit="%"
          trend="down"
          change_pct={-2.3}
          sparkline={[10, 11, 12, 14, 12, 11]}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <BarChart
            data={volatilityData}
            title="Monthly Volatility"
            bars={[{ key: 'volatility', fill: '#f59e0b', name: 'Volatility' }]}
            height={300}
          />
        </Card>
        <Card>
          <LineChart
            data={drawdownData}
            title="Maximum Drawdown"
            lines={[
              { key: 'drawdown', stroke: '#ef4444', name: 'Drawdown %' },
            ]}
            height={300}
          />
        </Card>
      </div>

      {/* Correlation Matrix */}
      <Card>
        <Table
          columns={correlationColumns}
          data={[
            { asset: 'India-US', correlation: 0.45, change: 0.08, trend: 'Increasing' },
            { asset: 'India-Europe', correlation: 0.38, change: 0.05, trend: 'Stable' },
            { asset: 'US-Europe', correlation: 0.72, change: -0.03, trend: 'Decreasing' },
            { asset: 'US-Japan', correlation: 0.55, change: 0.12, trend: 'Increasing' },
            { asset: 'Europe-Japan', correlation: 0.42, change: 0.02, trend: 'Stable' },
          ]}
          title="Asset Correlation Matrix"
          sortable
        />
      </Card>

      {/* Risk Metrics Summary */}
      <Card>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-neutral-600 dark:text-neutral-400">Sharpe Ratio</div>
            <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
              {risk.sharpe_ratio.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-sm text-neutral-600 dark:text-neutral-400">Sortino Ratio</div>
            <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
              {(risk.sharpe_ratio * 1.2).toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-sm text-neutral-600 dark:text-neutral-400">Calmar Ratio</div>
            <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
              {(risk.sharpe_ratio * 0.85).toFixed(2)}
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default RiskDashboard
