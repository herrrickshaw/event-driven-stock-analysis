import React from 'react'
import {
  LineChart as RechartLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts'
import { TimeSeriesData } from '@types/index'

interface LineChartProps {
  data: TimeSeriesData[]
  title?: string
  lines: {
    key: string
    stroke: string
    name?: string
    strokeDasharray?: string
  }[]
  height?: number
  showLegend?: boolean
  showGrid?: boolean
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

export const LineChart: React.FC<LineChartProps> = ({
  data,
  title,
  lines,
  height = 300,
  showLegend = true,
  showGrid = true,
}) => {
  return (
    <div className="w-full">
      {title && <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        <RechartLineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
          <XAxis dataKey="date" stroke="#6b7280" />
          <YAxis stroke="#6b7280" />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend />}
          {lines.map((line) => (
            <Line
              key={line.key}
              type="monotone"
              dataKey={line.key}
              stroke={line.stroke}
              name={line.name || line.key}
              strokeDasharray={line.strokeDasharray}
              dot={false}
              isAnimationActive={false}
            />
          ))}
        </RechartLineChart>
      </ResponsiveContainer>
    </div>
  )
}
