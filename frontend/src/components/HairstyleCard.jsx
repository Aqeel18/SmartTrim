import React from 'react'

export default function HairstyleCard({ item, onTry }) {
  return (
    <div className="group bg-white/5 border border-white/10 rounded-xl overflow-hidden shadow hover:shadow-cyan-500/10 transition">
      {/* eslint-disable-next-line jsx-a11y/alt-text */}
      <img src={item?.image} className="w-full h-40 object-cover group-hover:scale-[1.02] transition" />
      <div className="p-3 flex items-center justify-between">
        <div className="text-sm font-semibold">{item?.label || item?.name}</div>
        <button onClick={() => onTry?.(item)} className="px-3 py-1 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-bold transition">Try This</button>
      </div>
    </div>
  )
}

