import React from 'react'
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline'

export default function ErrorBanner({ message, onRetry }) {
  if (!message) return null
  return (
    <div className="mt-3 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-rose-800 dark:border-rose-400/30 dark:bg-rose-950/60 dark:text-rose-200">
      <ExclamationTriangleIcon className="w-5 h-5 mt-0.5 flex-shrink-0" />
      <div className="text-sm">
        <div className="font-semibold">Something went wrong</div>
        <div>{message}</div>
      </div>
      {onRetry && (
        <button onClick={onRetry} className="ml-auto inline-flex items-center gap-1 rounded-md border border-rose-200 dark:border-rose-400/30 px-2 py-1 text-xs text-rose-800 dark:text-rose-200 hover:bg-rose-100 dark:hover:bg-rose-900/60 transition">
          <ArrowPathIcon className="w-4 h-4" /> Retry
        </button>
      )}
    </div>
  )
}
