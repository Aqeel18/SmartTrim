import React from 'react'

export default function LoadingOverlay({ status }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-3 rounded-2xl bg-white/90 dark:bg-slate-900/90 border border-slate-200 dark:border-white/10 px-6 py-5 shadow-lg">
        <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
        <div className="text-sm font-medium text-slate-700 dark:text-slate-200">
          {status || 'AI analyzing facial geometry…'}
        </div>
      </div>
    </div>
  )
}
