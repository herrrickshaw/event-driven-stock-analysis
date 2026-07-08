import React from 'react'
import clsx from 'clsx'

interface CardProps {
  children: React.ReactNode
  className?: string
  title?: string
  subtitle?: string
  action?: React.ReactNode
  bordered?: boolean
  padding?: 'sm' | 'md' | 'lg'
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  title,
  subtitle,
  action,
  bordered = true,
  padding = 'md',
}) => {
  const paddingClasses = {
    sm: 'p-3',
    md: 'p-6',
    lg: 'p-8',
  }

  return (
    <div
      className={clsx(
        'bg-white dark:bg-neutral-800 rounded-lg shadow-card dark:shadow-none',
        bordered && 'border border-neutral-200 dark:border-neutral-700',
        paddingClasses[padding],
        className
      )}
    >
      {(title || subtitle || action) && (
        <div className="flex justify-between items-start mb-4">
          <div>
            {title && (
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">{subtitle}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
