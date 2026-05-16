import React from 'react'
import { motion } from 'framer-motion'
import { useAppContext } from '../context/AppContext.jsx'
import { CalendarIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline'

export default function History() {
  const { history } = useAppContext()

  return (
    <div className="min-h-screen pt-32 pb-12 px-6 max-w-7xl mx-auto">
      <div className="mb-16 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-5xl md:text-6xl font-display font-bold text-textMain mb-4 tracking-tight">Your <span className="text-primary font-light">Archive</span></h1>
          <p className="text-textMuted max-w-xl text-lg">A chronological record of your personalized grooming analyses and generated styles.</p>
        </div>
      </div>

      {history.length === 0 ? (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-16 rounded-[2rem] flex flex-col items-center justify-center text-center border-dashed border-2 border-textMain/10"
        >
          <div className="w-24 h-24 bg-surfaceHighlight rounded-full flex items-center justify-center mb-6 shadow-inner">
            <CalendarIcon className="w-10 h-10 text-textMuted" />
          </div>
          <h3 className="text-3xl font-display font-bold text-textMain mb-3">No Records Found</h3>
          <p className="text-textMuted max-w-md text-lg">
            Your archive is currently empty. Run an analysis to start building your personalized style history.
          </p>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {history.map((item, i) => (
            <motion.div 
              key={item.id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1, duration: 0.5, ease: "easeOut" }}
              whileHover={{ y: -10 }}
              className="glass-panel rounded-[2rem] overflow-hidden group shadow-xl hover:shadow-2xl hover:shadow-primary/5 transition-all duration-500"
            >
              <div className="aspect-[4/3] relative overflow-hidden bg-surface flex">
                <img src={item.originalUrl} alt="Original" className="w-1/2 h-full object-cover opacity-60 grayscale group-hover:grayscale-0 transition-all duration-700" />
                <img src={item.previewUrl} alt="Generated" className="w-1/2 h-full object-cover group-hover:scale-105 transition-transform duration-700" />
                
                {/* Center Divider Line */}
                <div className="absolute left-1/2 top-0 bottom-0 w-px bg-primary/30 z-10 shadow-[0_0_10px_var(--primary)]" />
                
                <div className="absolute inset-0 bg-gradient-to-t from-background via-background/20 to-transparent" />
                
                {/* Download Overlay */}
                <div className="absolute inset-0 bg-background/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center backdrop-blur-sm">
                   <a href={item.previewUrl} download={`smarttrim-${item.styleName}.png`} className="p-4 bg-primary text-black rounded-full hover:scale-110 transition-transform shadow-[0_0_20px_var(--primary-glow-end)] flex items-center justify-center gap-2 font-bold font-display uppercase tracking-widest text-xs">
                     <ArrowDownTrayIcon className="w-5 h-5" />
                     Download Look
                   </a>
                </div>
              </div>
              
              <div className="p-8 relative">
                <div className="absolute -top-6 right-8 w-12 h-12 bg-surface border border-textMain/10 rounded-2xl rotate-12 flex items-center justify-center shadow-lg group-hover:rotate-0 transition-transform duration-500">
                  <span className="text-primary font-bold font-display text-sm">V3</span>
                </div>
                
                <div className="text-xs text-primary font-bold tracking-[0.2em] uppercase mb-2">
                  Synthesized Look
                </div>
                <h4 className="text-2xl font-display font-bold text-textMain mb-2">{item.styleName}</h4>
                <div className="flex items-center gap-2 text-sm text-textMuted font-mono uppercase tracking-widest">
                  <CalendarIcon className="w-4 h-4" />
                  {new Date(item.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
