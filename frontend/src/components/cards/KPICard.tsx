import React from 'react'
import { Sparkline } from '@components/charts'
import clsx from 'clsx'

interface KPICardProps {
  name: string
  value: number | string
  unit: string
  target?: number
  change_pct?: number
  trend?: 'up' | 'down' | 'neutral'
  sparkline?: number[]
  alert?: {
    type: 'warning' | 'critical' | 'info'
    message: string
  }
}

export const KPICard: React.FC<KPICardProps> = ({
  name,
  value,
  unit,
  target,
  change_pct,
  trend = 'neutral',
  sparkline,
  alert,
}) => {
  const alertColors = {
    warning: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-700',
    critical: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-700',
    info: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700',
  }

  const changeColor = {
    up: 'text-green-600 dark:text-green-400',
    down: 'text-red-600 dark:text-red-400',
    neutral: 'text-gray-600 dark:text-gray-400',
  }

  return (
    <div
      className={clsx(
        'rounded-lg border p-4',
        alert
          ? alertColors[alert.type]
          : 'bg-white dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700'
      )}
    >
      <div className="flex justify-between items-start mb-3">
        <h4 className="text-sm font-medium text-neutral-600 dark:text-neutral-300">{name}</h4>
        {alert && (
          <span className="text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase">
            {alert.type}
          </span>
        )}
      </div>

      <div className="flex items-end justify-between mb-3">
        <div>
          <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            {typeof value === 'number' ? value.toFixed(2) : value}
            <span className="text-sm font-normal text-neutral-500 dark:text-neutral-400 ml-1">
              {unit}
            </span>
          </div>
          {change_pct !== undefined && (
            <div className={clsx('text-xs font-medium mt-1', changeColor[trend])}>
              {trend === 'up' ? '+' : trend === 'down' ? '-' : ''}
              {Math.abs(change_pct).toFixed(2)}% {trend !== 'neutral' ? `(${trend})` : ''}
            </div>
          )}
          {target !== undefined && (
            <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              Target: {target.toFixed(2)}
            </div>
          )}
        </div>
        {sparkline && <Sparkline data={sparkline} trend={trend} height={50} />}
      </div>

      {alert && <p className="text-xs text-gray-700 dark:text-gray-200">{alert.message}</p>}
    </div>
  )
}
