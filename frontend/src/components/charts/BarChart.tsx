import React from 'react'
import {
  BarChart as RechartBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts'

interface BarChartProps {
  data: any[]
  title?: string
  bars: {
    key: string
    fill: string
    name?: string
  }[]
  height?: number
  horizontal?: boolean
  showLegend?: boolean
}

const CustomTooltip: React.FC<TooltipProps<number, string>> = ({
  active,
  payload,
  label,
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded p-2 shadow-lg">
        <p className="text-xs text-neutral-300">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ color: entry.color }} className="text-xs font-medium">
            {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
          </p>
        ))}
      </div>
    )
  }
  return null
}

export const BarChart: React.FC<BarChartProps> = ({
  data,
  title,
  bars,
  height = 300,
  horizontal = false,
  showLegend = true,
}) => {
  return (
    <div className="w-full">
      {title && <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        <RechartBarChart
          data={data}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
          layout={horizontal ? 'vertical' : 'horizontal'}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          {!horizontal && <XAxis stroke="#6b7280" />}
          {!horizontal && <YAxis dataKey="name" stroke="#6b7280" width={80} />}
          {horizontal && <XAxis type="number" stroke="#6b7280" />}
          {horizontal && <YAxis dataKey="name" type="category" stroke="#6b7280" width={80} />}
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend />}
          {bars.map((bar) => (
            <Bar
              key={bar.key}
              dataKey={bar.key}
              fill={bar.fill}
              name={bar.name || bar.key}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </RechartBarChart>
      </ResponsiveContainer>
    </div>
  )
}
