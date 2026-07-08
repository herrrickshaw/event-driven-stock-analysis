import React, { useState } from 'react'
import clsx from 'clsx'

export interface Column<T> {
  key: keyof T | string
  header: string
  render?: (value: any, row: T) => React.ReactNode
  sortable?: boolean
  width?: string
  className?: string
}

interface TableProps<T> {
  data: T[]
  columns: Column<T>[]
  title?: string
  loading?: boolean
  pageSize?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export const Table = React.forwardRef<HTMLDivElement, TableProps<any>>(
  (
    { data, columns, title, loading = false, pageSize = 10, sortBy, sortOrder = 'asc' },
    ref
  ) => {
    const [currentPage, setCurrentPage] = useState(1)
    const [localSortBy, setLocalSortBy] = useState<string | undefined>(sortBy)
    const [localSortOrder, setLocalSortOrder] = useState<'asc' | 'desc'>(sortOrder)

    const sortedData = React.useMemo(() => {
      if (!localSortBy) return data

      return [...data].sort((a, b) => {
        const aVal = a[localSortBy as keyof typeof a]
        const bVal = b[localSortBy as keyof typeof b]

        if (aVal === bVal) return 0
        const comparison = aVal < bVal ? -1 : 1
        return localSortOrder === 'asc' ? comparison : -comparison
      })
    }, [data, localSortBy, localSortOrder])

    const paginatedData = sortedData.slice(
      (currentPage - 1) * pageSize,
      currentPage * pageSize
    )

    const totalPages = Math.ceil(sortedData.length / pageSize)

    const handleSort = (key: string) => {
      if (localSortBy === key) {
        setLocalSortOrder(localSortOrder === 'asc' ? 'desc' : 'asc')
      } else {
        setLocalSortBy(key)
        setLocalSortOrder('asc')
      }
      setCurrentPage(1)
    }

    return (
      <div ref={ref} className="w-full">
        {title && (
          <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            {title}
          </h3>
        )}

        <div className="overflow-x-auto border border-neutral-200 dark:border-neutral-700 rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50 dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-700">
              <tr>
                {columns.map((column) => (
                  <th
                    key={String(column.key)}
                    className={clsx(
                      'px-6 py-3 text-left font-medium text-neutral-700 dark:text-neutral-300',
                      column.width,
                      column.sortable && 'cursor-pointer hover:bg-neutral-100 dark:hover:bg-neutral-800'
                    )}
                    onClick={() => column.sortable && handleSort(String(column.key))}
                  >
                    <div className="flex items-center gap-2">
                      {column.header}
                      {column.sortable && (
                        <span className="text-xs">
                          {localSortBy === String(column.key)
                            ? localSortOrder === 'asc'
                              ? '↑'
                              : '↓'
                            : '~'}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={columns.length} className="px-6 py-8 text-center">
                    <div className="inline-block animate-spin">Loading...</div>
                  </td>
                </tr>
              ) : paginatedData.length === 0 ? (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="px-6 py-8 text-center text-neutral-500 dark:text-neutral-400"
                  >
                    No data available
                  </td>
                </tr>
              ) : (
                paginatedData.map((row, rowIdx) => (
                  <tr
                    key={rowIdx}
                    className="border-b border-neutral-200 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-800/50"
                  >
                    {columns.map((column) => (
                      <td
                        key={String(column.key)}
                        className={clsx(
                          'px-6 py-3 text-neutral-900 dark:text-neutral-100',
                          column.className
                        )}
                      >
                        {column.render
                          ? column.render(row[column.key as keyof typeof row], row)
                          : String(row[column.key as keyof typeof row])}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex justify-between items-center mt-4">
            <div className="text-sm text-neutral-600 dark:text-neutral-400">
              Page {currentPage} of {totalPages} ({sortedData.length} total)
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 rounded border border-neutral-300 dark:border-neutral-600 disabled:opacity-50 dark:disabled:opacity-30"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 rounded border border-neutral-300 dark:border-neutral-600 disabled:opacity-50 dark:disabled:opacity-30"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    )
  }
)

Table.displayName = 'Table'
