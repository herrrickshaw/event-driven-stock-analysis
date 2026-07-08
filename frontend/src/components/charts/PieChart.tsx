import React from 'react'
import {
  PieChart as RechartPieChart,
  Pie,
  Cell,
  Legend,
  Tooltip,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts'
import { DistributionData } from '@types/index'

interface PieChartProps {
  data: DistributionData[]
  title?: string
  colors: string[]
  height?: number
  showLegend?: boolean
}

const CustomTooltip: React.FC<TooltipProps<number, string>> = ({
  active,
  payload,
}) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload as DistributionData
    return (
      <div className="bg-neutral-800 border border-neutral-700 rounded p-2 shadow-lg">
        <p className="text-xs text-neutral-300">{data.name}</p>
        <p className="text-xs font-medium text-neutral-100">
          {data.value.toFixed(2)} ({data.percentage.toFixed(1)}%)
        </p>
      </div>
    )
  }
  return null
}

export const PieChart: React.FC<PieChartProps> = ({
  data,
  title,
  colors,
  height = 300,
  showLegend = true,
}) => {
  return (
    <div className="w-full">
      {title && (
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
          {title}
        </h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <RechartPieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percentage }) => `${name} ${percentage.toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend />}
        </RechartPieChart>
      </ResponsiveContainer>
    </div>
  )
}
