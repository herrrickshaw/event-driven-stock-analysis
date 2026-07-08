import React from 'react'

interface ErrorProps {
  message: string
  onRetry?: () => void
}

export const Error: React.FC<ErrorProps> = ({ message, onRetry }) => {
  return (
    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4 mb-4">
      <div className="flex items-start gap-3">
        <div className="text-red-600 dark:text-red-400 font-semibold">Error</div>
        <div className="flex-1">
          <p className="text-red-700 dark:text-red-300 text-sm">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-2 text-sm px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
