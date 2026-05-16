import React, { useState, useRef } from 'react'
import { motion } from 'framer-motion'

export default function PreviewPanel({ originalUrl, previewUrl, onReset, onDownload }) {
  const [sliderPosition, setSliderPosition] = useState(50)
  const [isDragging, setIsDragging] = useState(false)
  const [viewMode, setViewMode] = useState('slider') // 'slider' or 'side'
  const containerRef = useRef(null)

  const handleMove = (clientX) => {
    if (!containerRef.current || viewMode !== 'slider') return
    const rect = containerRef.current.getBoundingClientRect()
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width))
    const percentage = (x / rect.width) * 100
    setSliderPosition(percentage)
  }

  const onMouseMove = (e) => {
    if (!isDragging) return
    handleMove(e.clientX)
  }

  const onTouchMove = (e) => {
    if (!isDragging) return
    handleMove(e.touches[0].clientX)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-end mb-4">
        {previewUrl && (
          <div className="flex bg-surfaceHighlight/50 p-1 rounded-full border border-white/10">
            <button 
              onClick={() => setViewMode('slider')}
              className={`px-3 py-1 text-[10px] font-bold uppercase rounded-full transition-all ${viewMode === 'slider' ? 'bg-primary text-black' : 'text-textMuted hover:text-textMain'}`}
            >
              Slider
            </button>
            <button 
              onClick={() => setViewMode('side')}
              className={`px-3 py-1 text-[10px] font-bold uppercase rounded-full transition-all ${viewMode === 'side' ? 'bg-primary text-black' : 'text-textMuted hover:text-textMain'}`}
            >
              Side-by-Side
            </button>
          </div>
        )}
      </div>
      
      <div className="flex-1 relative rounded-3xl overflow-hidden border border-white/5 bg-black/20 backdrop-blur-xl shadow-2xl flex flex-col justify-center items-center min-h-[450px]">
        {previewUrl && originalUrl ? (
          <div className="w-full h-full p-4 flex flex-col items-center justify-center">
            {viewMode === 'slider' ? (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="relative w-full h-full max-h-[550px] select-none cursor-ew-resize rounded-2xl overflow-hidden shadow-2xl border border-white/10 bg-black/40"
                ref={containerRef}
                onMouseMove={onMouseMove}
                onMouseUp={() => setIsDragging(false)}
                onMouseLeave={() => setIsDragging(false)}
                onTouchMove={onTouchMove}
                onTouchEnd={() => setIsDragging(false)}
                onMouseDown={(e) => {
                  setIsDragging(true)
                  handleMove(e.clientX)
                }}
                onTouchStart={(e) => {
                  setIsDragging(true)
                  handleMove(e.touches[0].clientX)
                }}
              >
                {/* Base Image (Generated) */}
                <img src={previewUrl} alt="Generated" className="absolute inset-0 w-full h-full object-contain pointer-events-none" />
                
                {/* Top Image (Original) cropped */}
                <img 
                  src={originalUrl} 
                  alt="Original" 
                  className="absolute inset-0 w-full h-full object-contain pointer-events-none" 
                  style={{ clipPath: `polygon(0 0, ${sliderPosition}% 0, ${sliderPosition}% 100%, 0 100%)` }}
                />

                <div 
                  className="absolute top-0 bottom-0 w-0.5 bg-primary shadow-[0_0_15px_var(--primary)] pointer-events-none"
                  style={{ left: `${sliderPosition}%` }}
                >
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full shadow-xl flex items-center justify-center border-2 border-primary">
                    <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M8 9l4-4 4 4m0 6l-4 4-4-4" transform="rotate(90 12 12)" />
                    </svg>
                  </div>
                </div>

                <div className="absolute bottom-4 left-4 px-3 py-1 bg-black/60 backdrop-blur-md text-white text-[10px] font-bold rounded-full uppercase tracking-widest border border-white/10">Before</div>
                <div className="absolute bottom-4 right-4 px-3 py-1 bg-primary text-black text-[10px] font-bold rounded-full uppercase tracking-widest">After</div>
              </motion.div>
            ) : (
              <motion.div 
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="grid grid-cols-2 gap-4 w-full h-full max-h-[550px]"
              >
                <div className="relative rounded-2xl overflow-hidden border border-white/10 shadow-xl group bg-black/40">
                  <img src={originalUrl} alt="Original" className="w-full h-full object-contain" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent pointer-events-none" />
                  <div className="absolute bottom-4 left-4 px-3 py-1 bg-white/10 backdrop-blur-md rounded-full text-[10px] font-bold text-white uppercase tracking-widest border border-white/10">Original</div>
                </div>
                <div className="relative rounded-2xl overflow-hidden border-2 border-primary/30 shadow-[0_0_30px_var(--primary-glow-start)] group bg-black/40">
                  <img src={previewUrl} alt="Generated" className="w-full h-full object-contain" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent pointer-events-none" />
                  <div className="absolute bottom-4 left-4 px-3 py-1 bg-primary text-black rounded-full text-[10px] font-bold uppercase tracking-widest">Modified</div>
                </div>
              </motion.div>
            )}
          </div>
        ) : originalUrl ? (
          <div className="w-full h-full p-6 flex flex-col items-center justify-center">
            <div className="relative max-w-[320px] aspect-[3/4] rounded-2xl overflow-hidden shadow-2xl border border-white/10 group bg-black/40">
              <img src={originalUrl} alt="Original" className="w-full h-full object-contain opacity-60 group-hover:opacity-100 transition-opacity" />
              <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                <div className="px-6 py-3 bg-black/60 backdrop-blur-xl rounded-2xl border border-white/10 text-white font-display font-bold uppercase tracking-widest animate-pulse">
                  Ready to Process
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-textMuted flex flex-col items-center gap-4 opacity-40">
             <div className="w-20 h-20 rounded-full border-2 border-dashed border-textMuted flex items-center justify-center">
                <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
             </div>
             <p className="font-display font-bold uppercase tracking-[0.2em] text-xs">Awaiting Matrix Input</p>
          </div>
        )}
      </div>

      <div className="flex gap-4 mt-6">
        <button 
          disabled={!previewUrl} 
          onClick={onDownload} 
          className="flex-1 py-4 bg-primary text-black font-bold rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_0_20px_var(--primary-glow-start)] uppercase text-xs tracking-widest disabled:opacity-30 disabled:shadow-none"
        >
          Export Result
        </button>
        <button 
          disabled={!originalUrl && !previewUrl} 
          onClick={onReset} 
          className="px-8 py-4 border border-white/10 rounded-xl hover:bg-white/5 text-textMain font-bold transition-all uppercase text-xs tracking-widest disabled:opacity-30"
        >
          Reset
        </button>
      </div>
    </div>
  )
}
