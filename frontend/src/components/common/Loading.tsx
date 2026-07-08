import React from 'react'

export const Loading: React.FC<{ message?: string }> = ({ message = 'Loading...' }) => {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="inline-block animate-spin mb-4">
          <div className="h-12 w-12 border-4 border-primary-500 border-t-transparent rounded-full" />
        </div>
        <p className="text-neutral-600 dark:text-neutral-400">{message}</p>
      </div>
    </div>
  )
}
