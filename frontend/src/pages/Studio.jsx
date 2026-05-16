import React, { useState, useEffect, useRef, useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppContext } from '../context/AppContext.jsx'
import { submitPreviewJob, connectJobSocket, generatePreview } from '../api.js'
import PreviewPanel from '../components/PreviewPanel.jsx'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'

// ─── Animated progress bar component ─────────────────────────────────────────

function GenerationOverlay({ progress, message }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-background/70 backdrop-blur-md rounded-[2rem] border border-textMain/5"
    >
      {/* Spinner */}
      <div className="relative w-24 h-24 mb-8">
        <svg className="w-full h-full text-primary/20 animate-spin" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="2" />
        </svg>
        <svg className="w-full h-full text-primary absolute top-0 left-0 animate-spin" viewBox="0 0 100 100" style={{ animationDuration: '1.5s' }}>
          <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="100 200" strokeLinecap="round" />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center text-primary">
          <span className="text-sm font-bold font-mono">{progress}%</span>
        </div>
      </div>

      <h3 className="text-2xl font-display font-bold tracking-[0.2em] text-textMain uppercase mb-3">
        Synthesizing Pixels
      </h3>
      <p className="text-primary font-mono text-xs uppercase tracking-widest mb-6">{message || 'Running AI pipeline...'}</p>

      {/* Progress bar */}
      <div className="w-64 h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/10">
        <motion.div
          className="h-full bg-primary rounded-full shadow-[0_0_10px_var(--primary)]"
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        />
      </div>
    </motion.div>
  )
}

// ─── Main Studio page ─────────────────────────────────────────────────────────

export default function Studio() {
  const { state } = useLocation()
  const navigate  = useNavigate()
  const { uploadedImage, uploadedUrl, recommendedStyles, allStyles, history, saveToHistory } = useAppContext()

  const initialStyle = state?.selectedStyle
    || (recommendedStyles.length > 0 ? recommendedStyles[0].value : (allStyles.length > 0 ? allStyles[0].value : ''))

  const [selectedStyle, setSelectedStyle] = useState(initialStyle)
  const [isGenerating, setIsGenerating]   = useState(false)
  const [progress, setProgress]           = useState(0)
  const [progressMsg, setProgressMsg]     = useState('Queued')
  const [generatedUrl, setGeneratedUrl]   = useState(null)
  const [error, setError]                 = useState(null)

  const wsRef = useRef(null)

  useEffect(() => {
    if (!uploadedImage) { navigate('/upload'); return }
    if (uploadedImage && selectedStyle) handleGenerate(selectedStyle)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup WebSocket on unmount
  useEffect(() => () => wsRef.current?.close(), [])

  const handleGenerate = async (styleValue) => {
    // Close any existing socket
    wsRef.current?.close()

    setSelectedStyle(styleValue)
    setIsGenerating(true)
    setProgress(0)
    setProgressMsg('Submitting job...')
    setError(null)
    setGeneratedUrl(null)

    try {
      // 1. Submit the async job
      const { job_id } = await submitPreviewJob({ imageFile: uploadedImage, hairstyle: styleValue })

      setProgressMsg('Job queued...')

      // 2. Open WebSocket for live progress
      const ws = connectJobSocket(job_id, {
        onProgress: (job) => {
          setProgress(job.progress ?? 0)
          setProgressMsg(job.message || 'Processing...')
        },
        onDone: (base64Jpeg) => {
          // Convert base64 → object URL
          const byteChars  = atob(base64Jpeg)
          const byteNums   = new Uint8Array(byteChars.length).map((_, i) => byteChars.charCodeAt(i))
          const blob       = new Blob([byteNums], { type: 'image/jpeg' })
          const url        = URL.createObjectURL(blob)

          setGeneratedUrl(url)
          setIsGenerating(false)
          setProgress(100)

          const styleInfo = [...recommendedStyles, ...allStyles].find(s => s.value === styleValue)
          saveToHistory({
            id:          Date.now(),
            originalUrl: uploadedUrl,
            previewUrl:  url,
            styleName:   (styleInfo?.name || styleValue)
              .replace(/^.*[/\\]/, '').replace(/\.png$/i, '').replace(/_/g, ' '),
            date: new Date().toISOString(),
          })
        },
        onError: async (msg) => {
          console.warn('[Studio] WebSocket error, falling back to sync:', msg)
          // Fallback: synchronous /preview
          try {
            const blob = await generatePreview({ imageFile: uploadedImage, hairstyle: styleValue })
            const url  = URL.createObjectURL(blob)
            setGeneratedUrl(url)
            const styleInfo = [...recommendedStyles, ...allStyles].find(s => s.value === styleValue)
            saveToHistory({
              id:          Date.now(),
              originalUrl: uploadedUrl,
              previewUrl:  url,
              styleName:   (styleInfo?.name || styleValue)
                .replace(/^.*[/\\]/, '').replace(/\.png$/i, '').replace(/_/g, ' '),
              date: new Date().toISOString(),
            })
          } catch (fallbackErr) {
            setError(fallbackErr.message || 'Generation failed.')
          } finally {
            setIsGenerating(false)
          }
        },
      })

      wsRef.current = ws
    } catch (err) {
      // submitPreviewJob itself failed
      setError(err.message || 'Failed to submit job.')
      setIsGenerating(false)
    }
  }

  const handleDownload = () => {
    if (!generatedUrl) return
    const a        = document.createElement('a')
    a.href         = generatedUrl
    const safeName = selectedStyle.replace(/\.png$/i, '').replace(/[/\\]/g, '-')
    a.download     = `smarttrim-${safeName}.jpg`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  const sidebarStyles = useMemo(() => {
    const dedup = new Map()
    recommendedStyles.forEach(s => dedup.set(s.value, { ...s, isRecommended: true }))
    allStyles.forEach(s => { if (!dedup.has(s.value)) dedup.set(s.value, { ...s, isRecommended: false }) })
    return Array.from(dedup.values())
  }, [recommendedStyles, allStyles])

  return (
    <div className="flex h-screen bg-background overflow-hidden">

      {/* ── Left Sidebar — Style Selector ── */}
      <motion.div
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="w-80 bg-surface/50 backdrop-blur-2xl border-r border-textMain/10 flex flex-col h-full z-20 hidden md:flex shadow-2xl relative"
      >
        <div className="p-8 border-b border-textMain/5 flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 bg-textMain/5 hover:bg-textMain/10 rounded-full transition-colors border border-textMain/10">
            <ArrowLeftIcon className="w-5 h-5 text-textMain" />
          </button>
          <h2 className="text-2xl font-display font-bold text-textMain tracking-wide uppercase">Studio</h2>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
          {sidebarStyles.map((styleInfo) => {
            const isSelected = selectedStyle === styleInfo.value
            return (
              <div
                key={styleInfo.value}
                id={`style-${styleInfo.value.replace(/[^a-z0-9]/gi, '-')}`}
                onClick={() => { if (!isGenerating) handleGenerate(styleInfo.value) }}
                className={`flex items-center gap-4 p-3 rounded-2xl cursor-pointer transition-all duration-300 relative overflow-hidden group border
                  ${isSelected ? 'bg-primary/10 border-primary/30 shadow-[0_0_15px_var(--primary-glow-start)]' : 'bg-surface hover:bg-surfaceHighlight border-transparent'}
                  ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                {isSelected && <motion.div layoutId="sidebar-active" className="absolute inset-0 bg-primary/5 rounded-2xl" />}

                <div className="relative w-14 h-14 shrink-0 rounded-xl overflow-hidden border border-white/5 z-10">
                  <img src={styleInfo.image_url} alt={styleInfo.name} className="w-full h-full object-cover transition-transform group-hover:scale-110" />
                  {styleInfo.isRecommended && (
                    <div className="absolute top-0 left-0 bg-primary w-2 h-2 rounded-br-md shadow-[0_0_5px_var(--primary)]" />
                  )}
                </div>

                <div className="relative z-10 min-w-0 flex-1">
                  <p className={`font-bold font-display text-sm truncate ${isSelected ? 'text-primary' : 'text-textMain'}`}>
                    {(styleInfo.name || styleInfo.value).replace(/^.*[/\\]/, '').replace(/\.png$/i, '').replace(/_/g, ' ')}
                  </p>
                  <p className="text-[9px] font-semibold uppercase tracking-widest text-textMuted mt-1 truncate">
                    {styleInfo.isRecommended ? '✦ AI Match' : (styleInfo.category || 'General')}
                  </p>
                  {/* CLIP score badge */}
                  {styleInfo.score != null && (
                    <div className="mt-1 flex items-center gap-1">
                      <div className="h-0.5 rounded-full bg-primary/20 flex-1">
                        <div className="h-full bg-primary rounded-full" style={{ width: `${Math.round(styleInfo.score * 350)}%`, maxWidth: '100%' }} />
                      </div>
                      <span className="text-[8px] text-primary font-mono">{(styleInfo.score * 100).toFixed(0)}%</span>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </motion.div>

      {/* ── Main Preview Area ── */}
      <div className="flex-1 relative flex flex-col items-center justify-center p-6 md:p-12 overflow-y-auto bg-[radial-gradient(ellipse_at_center,_var(--surface-highlight),_transparent_70%)]">
        {/* Mobile back button */}
        <div className="md:hidden absolute top-6 left-6 z-30">
          <button onClick={() => navigate(-1)} className="p-3 bg-surface/80 backdrop-blur-md rounded-full border border-textMain/10 shadow-lg">
            <ArrowLeftIcon className="w-5 h-5 text-textMain" />
          </button>
        </div>

        {error && (
          <div className="absolute top-10 bg-red-500/10 text-red-400 px-6 py-3 rounded-full border border-red-500/20 backdrop-blur-md z-30 font-bold shadow-lg text-sm">
            ⚠ {error}
          </div>
        )}

        <div className="w-full max-w-5xl h-full flex items-center justify-center relative z-10">
          <AnimatePresence mode="wait">
            {isGenerating && (
              <GenerationOverlay key="overlay" progress={progress} message={progressMsg} />
            )}
          </AnimatePresence>

          <motion.div
            key={selectedStyle}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="w-full h-full"
          >
            <PreviewPanel
              originalUrl={uploadedUrl}
              previewUrl={generatedUrl}
              onReset={() => navigate('/upload')}
              onDownload={handleDownload}
            />
          </motion.div>
        </div>
      </div>

      {/* ── Right Sidebar — Session History ── */}
      <motion.div
        initial={{ x: 100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="w-64 bg-surface/30 backdrop-blur-3xl border-l border-white/5 h-full hidden lg:flex flex-col z-20"
      >
        <div className="p-6 border-b border-white/5">
          <h3 className="text-xs font-bold text-textMuted uppercase tracking-[0.2em]">Recent Creations</h3>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
          {history.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-4">
              <div className="w-10 h-10 rounded-full border border-dashed border-white/10 mb-4 flex items-center justify-center text-white/10">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <p className="text-[10px] text-textMuted uppercase tracking-widest leading-relaxed">No generations this session.</p>
            </div>
          ) : (
            history.slice().reverse().map((item) => (
              <motion.div
                key={item.id}
                whileHover={{ scale: 1.02 }}
                onClick={() => setGeneratedUrl(item.previewUrl)}
                className="relative group cursor-pointer aspect-square rounded-xl overflow-hidden border border-white/5 hover:border-primary/50 transition-all shadow-lg"
              >
                <img src={item.previewUrl} alt={item.styleName} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="absolute bottom-2 left-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <p className="text-[10px] font-bold text-white truncate capitalize">{item.styleName}</p>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </motion.div>
    </div>
  )
}
