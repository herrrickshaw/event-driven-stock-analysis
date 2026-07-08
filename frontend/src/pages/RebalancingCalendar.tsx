import React, { useEffect } from 'react'
import { Card, KPICard } from '@components/cards'
import { Table, Column } from '@components/tables'
import { Loading, Error } from '@components/common'
import { useAppDispatch, useAppSelector } from '@store/hooks'
import { setLoading, setError } from '@store/slices/dashboardSlice'
import apiService from '@services/api'
import type { RebalancingSchedule, AllocationDrift } from '@types/index'

const RebalancingCalendar: React.FC = () => {
  const dispatch = useAppDispatch()
  const { rebalancing, allocation_drift, loading, error } = useAppSelector(
    (state) => state.dashboard
  )

  useEffect(() => {
    const fetchData = async () => {
      dispatch(setLoading(true))
      try {
        await Promise.all([
          apiService.getRebalancingSchedule(),
          apiService.getAllocationDrift(),
        ])
      } catch (err) {
        dispatch(setError(err instanceof Error ? err.message : 'Failed to fetch rebalancing data'))
      } finally {
        dispatch(setLoading(false))
      }
    }

    fetchData()
  }, [dispatch])

  if (loading) return <Loading message="Loading rebalancing data..." />

  const scheduleColumns: Column<RebalancingSchedule>[] = [
    { key: 'scheduled_date', header: 'Scheduled Date', sortable: true },
    { key: 'frequency', header: 'Frequency', sortable: true },
    {
      key: 'status',
      header: 'Status',
      render: (val) => (
        <span
          className={`px-2 py-1 rounded text-xs font-medium ${
            val === 'completed'
              ? 'bg-green-100 text-green-700'
              : val === 'in-progress'
                ? 'bg-blue-100 text-blue-700'
                : val === 'failed'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-gray-100 text-gray-700'
          }`}
        >
          {val}
        </span>
      ),
    },
  ]

  const driftColumns: Column<AllocationDrift>[] = [
    { key: 'market', header: 'Market', render: (val) => val.toUpperCase() },
    { key: 'target', header: 'Target %', render: (val) => val.toFixed(2) },
    { key: 'current', header: 'Current %', render: (val) => val.toFixed(2) },
    {
      key: 'drift',
      header: 'Drift (pp)',
      render: (val) => (
        <span className={val > 0 ? 'text-red-600' : 'text-green-600'}>
          {val > 0 ? '+' : ''}{val.toFixed(2)}
        </span>
      ),
    },
    {
      key: 'threshold_exceeded',
      header: 'Alert',
      render: (val) => (
        <span className={val ? 'text-red-600 font-bold' : 'text-green-600'}>
          {val ? 'Exceeded' : 'OK'}
        </span>
      ),
    },
  ]

  // Mock data
  const mockSchedules: RebalancingSchedule[] = [
    {
      id: '1',
      scheduled_date: '2024-07-15',
      frequency: 'quarterly',
      status: 'completed',
      target_allocation: { india: 30, us: 40, europe: 20, japan: 5, korea: 5 },
      actual_allocation: { india: 31, us: 39, europe: 20, japan: 5, korea: 5 },
      drift_tolerance: 2,
    },
    {
      id: '2',
      scheduled_date: '2024-10-15',
      frequency: 'quarterly',
      status: 'pending',
      target_allocation: { india: 30, us: 40, europe: 20, japan: 5, korea: 5 },
      drift_tolerance: 2,
    },
  ]

  const mockDrift: AllocationDrift[] = [
    { market: 'india', target: 30, current: 32.5, drift: 2.5, threshold_exceeded: true },
    { market: 'us', target: 40, current: 39.2, drift: -0.8, threshold_exceeded: false },
    { market: 'europe', target: 20, current: 19.8, drift: -0.2, threshold_exceeded: false },
    { market: 'japan', target: 5, current: 5.1, drift: 0.1, threshold_exceeded: false },
    { market: 'korea', target: 5, current: 3.4, drift: -1.6, threshold_exceeded: false },
  ]

  const nextRebalanceDate = rebalancing.length > 0 ? rebalancing[0].scheduled_date : '2024-10-15'
  const daysUntilRebalance = Math.ceil(
    (new Date(nextRebalanceDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
  )

  return (
    <div className="space-y-6">
      {error && <Error message={error} />}

      {/* Rebalancing KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          name="Days to Rebalance"
          value={Math.max(0, daysUntilRebalance)}
          unit="days"
          trend="neutral"
        />
        <KPICard
          name="Max Drift"
          value={Math.max(...allocation_drift.map((d) => Math.abs(d.drift)))}
          unit="pp"
          target={2}
          alert={
            mockDrift[0].threshold_exceeded
              ? { type: 'warning', message: 'India allocation exceeds threshold' }
              : undefined
          }
        />
        <KPICard
          name="Drifted Markets"
          value={allocation_drift.filter((d) => d.threshold_exceeded).length}
          unit="markets"
          trend="down"
        />
        <KPICard
          name="Rebalances (YTD)"
          value={3}
          unit=""
          trend="neutral"
        />
      </div>

      {/* Drift Alert */}
      {mockDrift.some((d) => d.threshold_exceeded) && (
        <Card className="bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-700">
          <div className="flex items-start gap-3">
            <div className="text-yellow-600 dark:text-yellow-400 font-bold text-lg">!</div>
            <div>
              <h4 className="font-semibold text-yellow-900 dark:text-yellow-100">
                Allocation Drift Alert
              </h4>
              <p className="text-sm text-yellow-800 dark:text-yellow-200 mt-1">
                India allocation has drifted +2.5pp above target. Consider rebalancing if next
                scheduled date is not too far.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Allocation Drift Table */}
      <Card>
        <Table columns={driftColumns} data={mockDrift} title="Current Allocation Drift" sortable />
      </Card>

      {/* Rebalancing Schedule */}
      <Card>
        <Table
          columns={scheduleColumns}
          data={mockSchedules}
          title="Rebalancing Schedule"
          sortable
        />
      </Card>

      {/* Rebalancing Rules */}
      <Card title="Rebalancing Rules">
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-900/50 rounded">
            <div>
              <div className="font-medium text-neutral-900 dark:text-neutral-100">
                Frequency
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">Quarterly</div>
            </div>
          </div>
          <div className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-900/50 rounded">
            <div>
              <div className="font-medium text-neutral-900 dark:text-neutral-100">
                Drift Tolerance
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">2.0 percentage points</div>
            </div>
          </div>
          <div className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-900/50 rounded">
            <div>
              <div className="font-medium text-neutral-900 dark:text-neutral-100">
                Minimum Trade Size
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">$1,000</div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default RebalancingCalendar
