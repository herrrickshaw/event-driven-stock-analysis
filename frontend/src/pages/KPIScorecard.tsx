import React, { useEffect } from 'react'
import { Card, KPICard } from '@components/cards'
import { Table, Column } from '@components/tables'
import { Loading, Error } from '@components/common'
import { useAppDispatch, useAppSelector } from '@store/hooks'
import { updateKPIs, setLoading, setError } from '@store/slices/dashboardSlice'
import apiService from '@services/api'
import type { KPI } from '@types/index'

const KPIScorecard: React.FC = () => {
  const dispatch = useAppDispatch()
  const { kpis, loading, error } = useAppSelector((state) => state.dashboard)

  useEffect(() => {
    const fetchData = async () => {
      dispatch(setLoading(true))
      try {
        const data = await apiService.getKPIScorecard()
        dispatch(updateKPIs(data))
      } catch (err) {
        dispatch(setError(err instanceof Error ? err.message : 'Failed to fetch KPI data'))
      } finally {
        dispatch(setLoading(false))
      }
    }

    fetchData()
  }, [dispatch])

  if (loading) return <Loading message="Loading KPI data..." />

  const kpiColumns: Column<KPI>[] = [
    { key: 'name', header: 'KPI Name', sortable: true },
    {
      key: 'value',
      header: 'Current Value',
      render: (val, row) => `${val} ${row.unit}`,
    },
    {
      key: 'target',
      header: 'Target',
      render: (val) => (val ? `${val}` : '-'),
    },
    {
      key: 'change_pct',
      header: 'Change %',
      render: (val, row) => (
        <span
          className={
            row.trend === 'up'
              ? 'text-green-600'
              : row.trend === 'down'
                ? 'text-red-600'
                : 'text-gray-600'
          }
        >
          {val > 0 ? '+' : ''}{val.toFixed(2)}%
        </span>
      ),
    },
    {
      key: 'alert',
      header: 'Status',
      render: (val: any) => {
        if (!val) return <span className="text-green-600 font-bold">OK</span>
        return (
          <span
            className={
              val.type === 'critical'
                ? 'text-red-600 font-bold'
                : val.type === 'warning'
                  ? 'text-yellow-600 font-bold'
                  : 'text-blue-600'
            }
          >
            {val.type.toUpperCase()}
          </span>
        )
      },
    },
  ]

  // Mock KPI data
  const mockKPIs: KPI[] = [
    {
      id: '1',
      name: 'Portfolio Value',
      value: 1250000,
      unit: '$',
      change_pct: 5.2,
      trend: 'up',
      sparkline: [1000, 1050, 1100, 1120, 1180, 1250],
      target: 1300000,
    },
    {
      id: '2',
      name: 'Daily P&L',
      value: 2500,
      unit: '$',
      change_pct: 3.1,
      trend: 'up',
      sparkline: [1500, 1800, 2000, 2200, 2400, 2500],
    },
    {
      id: '3',
      name: 'Win Rate',
      value: 62,
      unit: '%',
      change_pct: 1.5,
      trend: 'up',
      sparkline: [58, 59, 60, 61, 62, 62],
      target: 65,
    },
    {
      id: '4',
      name: 'Profit Factor',
      value: 1.85,
      unit: '',
      change_pct: 0.8,
      trend: 'up',
      sparkline: [1.5, 1.6, 1.7, 1.8, 1.85, 1.85],
      target: 2.0,
    },
    {
      id: '5',
      name: 'Max Consecutive Losses',
      value: 3,
      unit: '',
      change_pct: -0.5,
      trend: 'down',
      sparkline: [5, 4, 4, 3, 3, 3],
      target: 2,
      alert: { type: 'warning', message: 'Slightly above target' },
    },
    {
      id: '6',
      name: 'Drawdown Duration',
      value: 12,
      unit: 'days',
      change_pct: 2.3,
      trend: 'down',
      sparkline: [18, 16, 15, 14, 12, 12],
      target: 10,
    },
    {
      id: '7',
      name: 'Trade Frequency',
      value: 24,
      unit: 'trades/day',
      change_pct: 5.1,
      trend: 'up',
      sparkline: [18, 19, 20, 22, 23, 24],
      target: 20,
    },
    {
      id: '8',
      name: 'Average Trade Duration',
      value: 45,
      unit: 'minutes',
      change_pct: -3.2,
      trend: 'down',
      sparkline: [52, 50, 48, 46, 45, 45],
      target: 40,
      alert: { type: 'info', message: 'Slightly above target' },
    },
    {
      id: '9',
      name: 'Correlation with Market',
      value: 0.42,
      unit: '',
      change_pct: 2.5,
      trend: 'up',
      sparkline: [0.35, 0.37, 0.39, 0.40, 0.42, 0.42],
      target: 0.35,
    },
    {
      id: '10',
      name: 'Execution Speed',
      value: 98,
      unit: '%',
      change_pct: 0.5,
      trend: 'up',
      sparkline: [95, 96, 97, 97, 98, 98],
      target: 99,
    },
    {
      id: '11',
      name: 'Slippage Cost',
      value: 0.12,
      unit: 'bps',
      change_pct: -8.3,
      trend: 'down',
      sparkline: [0.18, 0.16, 0.15, 0.14, 0.12, 0.12],
      target: 0.10,
    },
    {
      id: '12',
      name: 'Model Accuracy',
      value: 71,
      unit: '%',
      change_pct: 4.2,
      trend: 'up',
      sparkline: [62, 65, 67, 69, 70, 71],
      target: 75,
      alert: { type: 'info', message: 'Approaching target' },
    },
    {
      id: '13',
      name: 'Risk-Adjusted Return',
      value: 2.15,
      unit: '',
      change_pct: 3.5,
      trend: 'up',
      sparkline: [1.8, 1.9, 2.0, 2.1, 2.15, 2.15],
      target: 2.5,
    },
    {
      id: '14',
      name: 'Asset Utilization',
      value: 87,
      unit: '%',
      change_pct: 2.1,
      trend: 'up',
      sparkline: [82, 84, 85, 86, 87, 87],
      target: 90,
    },
    {
      id: '15',
      name: 'System Uptime',
      value: 99.95,
      unit: '%',
      change_pct: 0.02,
      trend: 'up',
      sparkline: [99.9, 99.92, 99.93, 99.94, 99.95, 99.95],
      target: 99.9,
    },
  ]

  const criticalAlerts = mockKPIs.filter((k) => k.alert?.type === 'critical')
  const warningAlerts = mockKPIs.filter((k) => k.alert?.type === 'warning')

  return (
    <div className="space-y-6">
      {error && <Error message={error} />}

      {/* Health Score */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="text-center">
            <div className="text-5xl font-bold text-primary-600 dark:text-primary-400 mb-2">
              {kpis?.health_score || 78}
            </div>
            <div className="text-sm text-neutral-600 dark:text-neutral-400">Overall Health Score</div>
            <div className="mt-2 text-xs text-green-600">+2.5% from last week</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-5xl font-bold text-yellow-600 mb-2">
              {warningAlerts.length}
            </div>
            <div className="text-sm text-neutral-600 dark:text-neutral-400">Warning Alerts</div>
            <div className="mt-2 text-xs text-yellow-600">Require attention</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-5xl font-bold text-red-600 mb-2">
              {criticalAlerts.length}
            </div>
            <div className="text-sm text-neutral-600 dark:text-neutral-400">Critical Alerts</div>
            <div className="mt-2 text-xs text-red-600">Immediate action</div>
          </div>
        </Card>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockKPIs.map((kpi) => (
          <KPICard
            key={kpi.id}
            name={kpi.name}
            value={kpi.value}
            unit={kpi.unit}
            target={kpi.target}
            change_pct={kpi.change_pct}
            trend={kpi.trend}
            sparkline={kpi.sparkline}
            alert={kpi.alert}
          />
        ))}
      </div>

      {/* Detailed KPI Table */}
      <Card>
        <Table
          columns={kpiColumns}
          data={mockKPIs}
          title="KPI Details"
          sortable
          pageSize={15}
        />
      </Card>

      {/* Alerts */}
      {(criticalAlerts.length > 0 || warningAlerts.length > 0) && (
        <Card title="Active Alerts">
          <div className="space-y-2">
            {criticalAlerts.map((kpi) => (
              <div
                key={kpi.id}
                className="flex items-start gap-3 p-3 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-700"
              >
                <div className="text-red-600 dark:text-red-400 font-bold">!</div>
                <div className="flex-1">
                  <div className="font-medium text-red-900 dark:text-red-100">{kpi.name}</div>
                  <div className="text-sm text-red-800 dark:text-red-200">
                    {kpi.alert?.message}
                  </div>
                </div>
              </div>
            ))}
            {warningAlerts.map((kpi) => (
              <div
                key={kpi.id}
                className="flex items-start gap-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded border border-yellow-200 dark:border-yellow-700"
              >
                <div className="text-yellow-600 dark:text-yellow-400 font-bold">!</div>
                <div className="flex-1">
                  <div className="font-medium text-yellow-900 dark:text-yellow-100">{kpi.name}</div>
                  <div className="text-sm text-yellow-800 dark:text-yellow-200">
                    {kpi.alert?.message}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

export default KPIScorecard
