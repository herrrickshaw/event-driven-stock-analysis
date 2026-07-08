import React from 'react'
import { LineChart, Line, ResponsiveContainer } from 'recharts'

interface SparklineProps {
  data: number[]
  color?: string
  height?: number
  trend?: 'up' | 'down' | 'neutral'
}

export const Sparkline: React.FC<SparklineProps> = ({
  data,
  color = '#0ea5e9',
  height = 40,
  trend,
}) => {
  if (!data || data.length === 0) {
    return <div className="w-full h-10 bg-neutral-100 dark:bg-neutral-900 rounded" />
  }

  // Convert data to chart format
  const chartData = data.map((value, index) => ({
    index,
    value,
  }))

  // Determine color based on trend if not provided
  let lineColor = color
  if (trend === 'up') {
    lineColor = '#10b981'
  } else if (trend === 'down') {
    lineColor = '#ef4444'
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={lineColor}
          dot={false}
          isAnimationActive={false}
          strokeWidth={2}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
