import React from 'react'

const colorByShape = {
  'Round': 'from-emerald-400 to-lime-400',
  'Oval': 'from-cyan-400 to-sky-400',
  'Oblong': 'from-amber-400 to-orange-400',
  'Diamond': 'from-fuchsia-400 to-pink-400',
}

export default function FaceShapeBadge({ shape }) {
  const gradient = colorByShape[shape] || 'from-slate-400 to-slate-500'
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gradient-to-r ${gradient} text-black font-semibold shadow shadow-black/30 animate-[fadeIn_0.4s_ease]`}>
      <span className="tracking-wide text-xs">{shape?.toUpperCase()} FACE</span>
    </div>
  )
}

