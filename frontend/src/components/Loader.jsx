import React from 'react'

export default function Loader({ label = 'Loading…' }) {
  return (
    <div className="flex items-center gap-3 text-slate-300">
      <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  )
}

