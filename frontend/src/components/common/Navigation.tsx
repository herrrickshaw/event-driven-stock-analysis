import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import clsx from 'clsx'

export const Navigation: React.FC = () => {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Performance' },
    { path: '/risk', label: 'Risk' },
    { path: '/rebalancing', label: 'Rebalancing' },
    { path: '/markets', label: 'Markets' },
    { path: '/kpis', label: 'KPIs' },
  ]

  return (
    <nav className="bg-white dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700 shadow-sm">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <div className="text-xl font-bold text-primary-600 dark:text-primary-400">
              EventDash
            </div>
            <div className="hidden md:flex gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={clsx(
                    'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    location.pathname === item.path
                      ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-200'
                      : 'text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700'
                  )}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-neutral-600 dark:text-neutral-400">
              Connected: <span className="text-green-600 dark:text-green-400">●</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
