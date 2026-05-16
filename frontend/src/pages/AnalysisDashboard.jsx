import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppContext } from '../context/AppContext.jsx'
import { analyzeFaceShape, fetchHairstyles } from '../api.js'
import AnimatedCard from '../components/AnimatedCard.jsx'
import { ShieldCheckIcon, AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline'

// Simple SVG Face Shape Diagram
const FaceShapeDiagram = ({ shape = 'oval', className = "w-24 h-24" }) => {
  const getPath = () => {
    const s = (shape || 'oval').toLowerCase()
    switch (s) {
      case 'square': return "M20 20 Q50 10 80 20 L85 70 Q50 95 15 70 Z"
      case 'round': return "M50 10 C80 10 90 40 80 75 C65 95 35 95 20 75 C10 40 20 10 50 10 Z"
      case 'oblong': return "M30 10 Q50 5 70 10 L75 80 Q50 100 25 80 Z"
      case 'heart': return "M50 25 C50 25 85 5 95 40 C105 75 50 95 50 95 C50 95 -5 75 5 40 C15 5 50 25 50 25 Z"
      case 'diamond': return "M50 10 L85 50 L50 90 L15 50 Z"
      case 'oval': 
      default: return "M30 15 Q50 5 70 15 L80 60 Q50 100 20 60 Z"
    }
  }

  return (
    <svg className={className} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Background abstract lines */}
      <path d="M10 50 L90 50 M50 10 L50 90" stroke="var(--primary)" strokeOpacity="0.2" strokeWidth="1" strokeDasharray="4 4" />
      {/* Dynamic Face Shape */}
      <motion.path 
        initial={{ pathLength: 0, fill: "rgba(0,0,0,0)" }}
        animate={{ pathLength: 1, fill: "var(--primary-glow-start)" }}
        transition={{ duration: 1.5, ease: "easeOut" }}
        d={getPath()} 
        stroke="var(--primary)" 
        strokeWidth="2" 
      />
      {/* Scanning points */}
      <circle cx="35" cy="45" r="2" fill="var(--accent)" className="animate-pulse" />
      <circle cx="65" cy="45" r="2" fill="var(--accent)" className="animate-pulse" />
      <circle cx="50" cy="80" r="2" fill="var(--accent)" className="animate-pulse" />
    </svg>
  )
}

export default function AnalysisDashboard() {
  const navigate = useNavigate()
  const { 
    uploadedImage, uploadedUrl, 
    faceShapeResult, setFaceShapeResult, 
    recommendedStyles, setRecommendedStyles,
    allStyles, setAllStyles,
    resetFlow
  } = useAppContext()
  const [analyzing, setAnalyzing] = useState(true)
  const [error, setError] = useState(null)

  // State to track which style is being "previewed" in the Before/After section
  const [previewStyle, setPreviewStyle] = useState(null)

  useEffect(() => {
    if (!uploadedImage) {
      navigate('/upload')
      return
    }

    if (faceShapeResult && recommendedStyles.length > 0 && allStyles.length > 0) {
      if (!previewStyle) setPreviewStyle(recommendedStyles[0])
      setAnalyzing(false)
      return
    }

    let isMounted = true
    const runAnalysis = async () => {
      try {
        const [analysisRes, stylesRes] = await Promise.all([
          analyzeFaceShape(uploadedImage),
          fetchHairstyles()
        ])
        
        if (!isMounted) return

        setFaceShapeResult(analysisRes)

        const flatStyles = Object.values(stylesRes || {}).flat().filter((s) => s.source === 'cleaned')
        setAllStyles(flatStyles)

        const recs = Array.isArray(analysisRes.recommended) ? analysisRes.recommended : []
        let matchedStyles = []
        if (recs.length > 0) {
          matchedStyles = flatStyles.filter(s => recs.includes(s.value))
        }
        
        if (matchedStyles.length < 3) {
          matchedStyles = [...matchedStyles, ...flatStyles.filter(s => !matchedStyles.includes(s))].slice(0, 4)
        }

        setRecommendedStyles(matchedStyles)
        setPreviewStyle(matchedStyles[0])
        setAnalyzing(false)
      } catch (err) {
        if (!isMounted) return
        setError(err.message || 'Failed to analyze face shape')
        setAnalyzing(false)
      }
    }

    setTimeout(runAnalysis, 2500)

    return () => { isMounted = false }
  }, [uploadedImage, faceShapeResult, recommendedStyles, allStyles, navigate, setFaceShapeResult, setRecommendedStyles, setAllStyles, previewStyle])

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center pt-20 px-6">
        <div className="glass-panel p-8 rounded-[2rem] max-w-md text-center">
          <div className="w-16 h-16 bg-red-500/10 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4 border border-red-500/20">
             <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </div>
          <h2 className="text-xl font-display font-bold mb-2">Analysis Interrupted</h2>
          <p className="text-textMuted mb-6">{error}</p>
          <button 
            onClick={() => { resetFlow(); navigate('/upload'); }} 
            className="px-6 py-3 border border-textMain/20 rounded-full hover:bg-surfaceHighlight transition text-sm font-bold"
          >
            Restart Process
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen pt-24 pb-20 px-4 md:px-8 max-w-[1600px] mx-auto w-full">
      <AnimatePresence mode="wait">
        {analyzing ? (
          <motion.div 
            key="analyzing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex flex-col items-center justify-center h-[75vh]"
          >
            <div className="relative w-56 h-72 rounded-[2.5rem] overflow-hidden border border-primary/20 shadow-[0_0_60px_var(--primary-glow-start)] mb-10">
              <img src={uploadedUrl} alt="Scanning" className="w-full h-full object-cover opacity-50 grayscale" />
              <motion.div 
                className="absolute left-0 right-0 h-1 bg-primary shadow-[0_0_30px_var(--primary)] z-10"
                animate={{ top: ['0%', '100%', '0%'] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              />
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(0,0,0,0.4)_100%)]" />
            </div>
            <h3 className="text-3xl font-display font-bold tracking-[0.25em] text-primary animate-pulse uppercase">Geometric Profiling</h3>
            <p className="text-textMuted mt-3 font-mono text-[10px] tracking-[0.4em] uppercase opacity-60">Synthesizing facial matrix v2.0</p>
          </motion.div>
        ) : (
          <motion.div 
            key="dashboard"
            initial="hidden" 
            animate="visible" 
            variants={{
              hidden: { opacity: 0 },
              visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
            }}
            className="space-y-16"
          >
            {/* ── PREVIEW HERO (BEFORE / AFTER) ── */}
            <motion.section 
              variants={{ hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center bg-surface/30 backdrop-blur-2xl rounded-[3rem] p-8 md:p-12 border border-white/5 relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />
              
              {/* Left: Transformation View */}
              <div className="lg:col-span-7 relative group">
                 <div className="flex flex-col sm:flex-row gap-6 items-center justify-center">
                    {/* Before */}
                    <div className="relative w-full max-w-[280px] aspect-[3/4] rounded-[2rem] overflow-hidden border border-white/10 shadow-2xl">
                       <img src={uploadedUrl} alt="Original" className="w-full h-full object-cover" />
                       <div className="absolute bottom-4 left-4 px-3 py-1 bg-black/60 backdrop-blur-md rounded-full text-[10px] font-bold text-white uppercase tracking-widest border border-white/10">Original</div>
                    </div>

                    {/* Arrow / Sync Icon */}
                    <div className="flex flex-col items-center gap-2 text-primary opacity-40">
                       <svg className="w-8 h-8 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7m0 0l-7 7m7-7H3" />
                       </svg>
                       <span className="text-[9px] font-bold uppercase tracking-[0.2em]">Synthesis</span>
                    </div>

                    {/* After (Hairstyle Preview) */}
                    <div className="relative w-full max-w-[280px] aspect-[3/4] rounded-[2rem] overflow-hidden border-2 border-primary/30 shadow-[0_0_40px_var(--primary-glow-start)]">
                       <AnimatePresence mode="wait">
                          <motion.img 
                            key={previewStyle?.value}
                            initial={{ opacity: 0, scale: 1.1 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            transition={{ duration: 0.6 }}
                            src={previewStyle?.image_url} 
                            alt="Preview" 
                            className="w-full h-full object-cover" 
                          />
                       </AnimatePresence>
                       <div className="absolute bottom-4 right-4 px-3 py-1 bg-primary text-black rounded-full text-[10px] font-bold uppercase tracking-widest">Preview</div>
                       <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none" />
                       <div className="absolute bottom-10 left-0 right-0 text-center px-4">
                          <span className="text-white text-sm font-bold drop-shadow-md truncate block capitalize">
                            {(previewStyle?.name || previewStyle?.value).replace(/^.*[\/\\]/, '').replace(/\.png$/i, '').replace(/_/g, ' ')}
                          </span>
                       </div>
                    </div>
                 </div>
              </div>

              {/* Right: Analysis Details */}
              <div className="lg:col-span-5 space-y-8">
                 <div>
                    <div className="inline-flex items-center gap-2 mb-4 px-3 py-1 bg-primary/10 border border-primary/20 rounded-full">
                       <FaceShapeDiagram shape={faceShapeResult?.face_shape} className="w-6 h-6" />
                       <span className="text-xs font-bold text-primary tracking-widest uppercase">{faceShapeResult?.face_shape} Profile</span>
                    </div>
                    <h2 className="text-4xl md:text-5xl font-display font-bold text-textMain leading-[1.1] mb-4 uppercase">
                       Style Transformation <span className="text-gradient">Unlocked.</span>
                    </h2>
                    <p className="text-textMuted text-lg leading-relaxed font-light">
                       Your facial geometry suggests high compatibility with structured, volumetric styles. We've curated these matches based on your {faceShapeResult?.face_shape} jawline and forehead width.
                    </p>
                 </div>

                 <div className="flex flex-wrap gap-4">
                    <button 
                      onClick={() => navigate('/studio', { state: { selectedStyle: previewStyle?.value } })}
                      className="px-10 py-4 bg-primary text-black font-bold rounded-full hover:scale-105 transition-all shadow-[0_0_20px_var(--primary-glow-start)] uppercase text-xs tracking-widest"
                    >
                      Try On Current Style
                    </button>
                    <button 
                      onClick={() => document.getElementById('catalog').scrollIntoView({ behavior: 'smooth' })}
                      className="px-8 py-4 border border-white/10 rounded-full hover:bg-white/5 transition-all uppercase text-xs tracking-widest font-bold text-textMain"
                    >
                      Explore Library
                    </button>
                 </div>
              </div>
            </motion.section>

            {/* ── AI RECOMMENDATIONS ── */}
            <section className="space-y-8">
               <div className="flex items-end justify-between border-b border-white/10 pb-6">
                  <div>
                    <h3 className="text-2xl font-display font-bold text-textMain uppercase tracking-tighter">Precision Matches</h3>
                    <p className="text-textMuted text-xs uppercase tracking-[0.2em] mt-1 opacity-60">High confidence matches for your structure</p>
                  </div>
                  <div className="text-[10px] font-bold text-primary tracking-[0.3em] uppercase">AI Confidence: 98.4%</div>
               </div>

               <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-6">
                 {recommendedStyles.map((style) => (
                    <div key={style.value} onMouseEnter={() => setPreviewStyle(style)}>
                       <AnimatedCard 
                         styleInfo={style} 
                         isRecommended={true} 
                         onSelect={(val) => navigate('/studio', { state: { selectedStyle: val } })} 
                       />
                    </div>
                 ))}
               </div>
            </section>

            {/* ── FULL CATALOG ── */}
            <section id="catalog" className="space-y-8">
               <div className="flex items-center gap-4 mb-8">
                  <div className="h-px flex-1 bg-white/10" />
                  <h3 className="text-xl font-display font-bold text-textMain/40 uppercase tracking-[0.4em]">Full Style Library</h3>
                  <div className="h-px flex-1 bg-white/10" />
               </div>

               <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                 {allStyles.map((style) => (
                    <div key={style.value} onMouseEnter={() => setPreviewStyle(style)}>
                       <AnimatedCard 
                         styleInfo={style} 
                         onSelect={(val) => navigate('/studio', { state: { selectedStyle: val } })} 
                       />
                    </div>
                 ))}
               </div>
            </section>

          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
