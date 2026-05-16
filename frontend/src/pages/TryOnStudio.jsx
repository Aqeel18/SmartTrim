import React, { useState, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import { generatePreview, fetchHairstyles, analyzeFaceShape } from '../api'
import UploadArea from '../components/UploadArea.jsx'
import PreviewPanel from '../components/PreviewPanel.jsx'
import ErrorBanner from '../components/ErrorBanner.jsx'
import LoadingOverlay from '../components/LoadingOverlay.jsx'
import FaceShapeBadge from '../components/FaceShapeBadge.jsx'

export default function TryOnStudio() {
  const [file, setFile] = useState(null)
  const [uploadedUrl, setUploadedUrl] = useState('')
  const [availableStyles, setAvailableStyles] = useState({})
  const [selectedStyle, setSelectedStyle] = useState('')
  const [faceShape, setFaceShape] = useState('')
  const [recommendedValues, setRecommendedValues] = useState([])
  const [recommendedReasons, setRecommendedReasons] = useState({})
  const [previewUrl, setPreviewUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadStyles() {
      try {
        const stylesData = await fetchHairstyles()
        setAvailableStyles(stylesData)
        const categories = Object.keys(stylesData)
        if (categories.length > 0) {
          const firstCategory = categories[0]
          if (stylesData[firstCategory].length > 0) {
            setSelectedStyle(stylesData[firstCategory][0].value)
          }
        }
      } catch (e) {
        console.error('Failed to load hairstyles:', e)
        setError('Could not load hairstyles from server.')
      }
    }
    loadStyles()
  }, [])

  const canGenerate = useMemo(() => !!file && !!selectedStyle && !loading, [file, selectedStyle, loading])

  const handleFileSelected = (f) => {
    setError('')
    setStatus('')
    setPreviewUrl('')
    setFile(f)
    if (uploadedUrl) URL.revokeObjectURL(uploadedUrl)
    if (f) setUploadedUrl(URL.createObjectURL(f))
    else setUploadedUrl('')

    if (f) {
      setStatus('AI analyzing facial geometry…')
      analyzeFaceShape(f)
        .then((res) => {
          setFaceShape(res.face_shape || '')
          setRecommendedValues(Array.isArray(res.recommended) ? res.recommended : [])
          setRecommendedReasons(res.reasons || {})
          setStatus('')
        })
        .catch((e) => {
          console.warn('Face shape analysis failed:', e)
          setFaceShape('')
          setRecommendedValues([])
          setRecommendedReasons({})
          setStatus('')
        })
    } else {
      setFaceShape('')
      setRecommendedValues([])
      setRecommendedReasons({})
    }
  }

  const displayStyles = useMemo(() => {
    if (!availableStyles || Object.keys(availableStyles).length === 0) return {}
    
    // Unified mapping for recommended check
    const allItems = Object.entries(availableStyles).flatMap(([cat, arr]) => arr.map((x) => ({ ...x, cat })))
    const byValue = new Map(allItems.map((x) => [x.value, x]))
    
    const recommended = []
    for (const val of (recommendedValues || [])) {
      if (byValue.has(val)) recommended.push(byValue.get(val))
    }
    
    const result = {}
    if (recommended.length > 0) result['Recommended'] = recommended
    for (const [cat, arr] of Object.entries(availableStyles)) {
      result[cat] = arr
    }
    return result
  }, [availableStyles, recommendedValues])

  const allItemsUnified = useMemo(() => {
    const arr = Object.values(availableStyles || {}).flat()
    const dedup = new Map()
    for (const it of arr) if (!dedup.has(it.value)) dedup.set(it.value, it)
    return Array.from(dedup.values()).sort((a, b) => (a.label || '').localeCompare(b.label || ''))
  }, [availableStyles])

  const selectedItem = useMemo(() => {
    const arr = Object.values(availableStyles || {}).flat()
    return arr.find((x) => x.value === selectedStyle) || null
  }, [availableStyles, selectedStyle])

  // No "show only recommended" mode; user can browse all and still see recommendations

  const handleGenerate = async () => {
    if (!file) return
    setLoading(true)
    setError('')
    setStatus('AI analyzing facial geometry…')
    try {
      const blob = await generatePreview({ imageFile: file, hairstyle: selectedStyle })
      setStatus('Rendering try-on preview…')
      const url = URL.createObjectURL(blob)
      setPreviewUrl(url)
      setStatus('')
    } catch (e) {
      setError('We couldn\'t generate the preview. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Ensures the button uses the clicked hairstyle, not the dropdown value
  const handleGenerateForStyle = async (styleValue) => {
    if (!file) return
    setSelectedStyle(styleValue)
    setLoading(true)
    setError('')
    setStatus('AI analyzing facial geometry…')
    try {
      const blob = await generatePreview({ imageFile: file, hairstyle: styleValue })
      setStatus('Rendering try-on preview…')
      const url = URL.createObjectURL(blob)
      setPreviewUrl(url)
      setStatus('')
    } catch (e) {
      setError('We couldn\'t generate the preview. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setError('')
    setStatus('')
    setPreviewUrl('')
    setFile(null)
    if (uploadedUrl) URL.revokeObjectURL(uploadedUrl)
    setUploadedUrl('')
    setFaceShape('')
    setRecommendedValues([])
    setRecommendedReasons({})
  }

  const handleDownload = async () => {
    if (!previewUrl) return
    try {
      const res = await fetch(previewUrl)
      const blob = await res.blob()
      const dlUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = dlUrl
      a.download = 'smarttrim360-preview.png'
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(dlUrl)
    } catch (e) {
      console.warn('Download failed', e)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
      <section className="space-y-6 flex flex-col">
        <div className="p-6 rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl shadow-2xl">
          <UploadArea onFileSelected={handleFileSelected} previewUrl={uploadedUrl} showPreview={!previewUrl} />
          <div className="mt-4">
            {faceShape && <FaceShapeBadge shape={faceShape} />}
            {recommendedValues?.length > 0 && (
              <div className="text-sm text-cyan-200 mt-2">Showing AI suggestions for <span className="font-bold">{faceShape}</span> face shape.</div>
            )}
          </div>
        </div>

        <div className="p-6 rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl shadow-2xl flex-1">
          <div className="flex items-center justify-between gap-3 mb-6">
            {selectedItem ? (
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-sm font-semibold shadow-inner" title={selectedItem.label}>
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span className="opacity-80">Selected:</span>
                <span className="truncate max-w-[180px]">{selectedItem.label}</span>
              </div>
            ) : (
              <div className="text-sm text-slate-400">Select a hairstyle to begin</div>
            )}
            <button 
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold shadow-lg shadow-cyan-500/25 transition-all disabled:opacity-50 disabled:shadow-none" 
              disabled={!canGenerate} 
              onClick={handleGenerate}
            >
              {loading ? 'Processing...' : 'Generate Preview'}
            </button>
          </div>
          {status && <div className="text-sm text-cyan-300 animate-pulse font-medium">{status}</div>}
          {error && <ErrorBanner message={error} onRetry={handleGenerate} />}

          {/* AI Recommended Section */}
          {recommendedValues?.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="h-5 w-1 bg-primary rounded-full shadow-[0_0_10px_var(--primary)]" />
                <h3 className="font-display font-bold text-lg text-textMain uppercase tracking-tight">AI Recommended</h3>
              </div>
              <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar px-1">
                {recommendedValues.map((val) => {
                  const all = Object.values(availableStyles || {}).flat().filter((x) => x.source === 'cleaned')
                  const item = all.find((x) => x.value === val)
                  if (!item) return null
                  const selected = item.value === selectedStyle
                  return (
                    <motion.div
                      key={val}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setSelectedStyle(val)}
                      className={`min-w-[140px] rounded-2xl transition-all duration-300 overflow-hidden cursor-pointer relative border-2 ${
                        selected 
                        ? 'border-primary shadow-[0_0_15px_var(--primary-glow-start)] bg-surfaceHighlight' 
                        : 'border-white/5 bg-white/5 hover:border-white/10'
                      }`}
                    >
                      <div className="aspect-square flex items-center justify-center p-1.5 relative">
                        {item.image_url ? (
                          <img src={item.image_url} alt={item.label} loading="lazy" className="w-full h-full object-cover rounded-xl" />
                        ) : (
                          <div className="text-[10px] text-textMuted uppercase font-bold tracking-widest text-center">No Preview</div>
                        )}
                        <div className="absolute top-2 left-2 bg-primary/90 text-black px-1.5 py-0.5 rounded-full text-[7px] font-black uppercase tracking-tighter">Match</div>
                      </div>
                      <div className="p-3 bg-gradient-to-t from-black/80 to-black/20">
                        <div className="text-xs font-display font-bold text-primary uppercase tracking-[0.15em] mb-0.5">Recommended</div>
                        <div className="text-sm font-semibold text-white truncate capitalize">{(item.label || item.value).replace(/^.*[\/\\]/, '').replace(/\.png$/i, '').replace(/_/g, ' ')}</div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Full Catalog Section */}
          {allItemsUnified.length > 0 && (
            <div className="mt-8">
              <div className="flex items-center gap-3 mb-3">
                <div className="h-5 w-1 bg-textMain/20 rounded-full" />
                <h3 className="font-display font-bold text-lg text-textMain uppercase tracking-tight">Full Catalog</h3>
              </div>
              <div className="flex gap-3 overflow-x-auto pb-4 custom-scrollbar px-1">
                {allItemsUnified.map((item) => {
                  const selected = item.value === selectedStyle
                  return (
                    <motion.div
                      key={item.value}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setSelectedStyle(item.value)}
                      className={`min-w-[110px] rounded-2xl transition-all duration-300 overflow-hidden cursor-pointer border ${
                        selected 
                        ? 'border-primary bg-surfaceHighlight shadow-md' 
                        : 'border-white/5 bg-white/5 hover:border-white/10'
                      }`}
                    >
                      <div className="aspect-square flex items-center justify-center p-1.5">
                        {item.image_url ? (
                          <img src={item.image_url} alt={item.label} loading="lazy" className="w-full h-full object-cover rounded-xl opacity-80 group-hover:opacity-100" />
                        ) : (
                          <div className="text-[8px] text-textMuted uppercase font-bold text-center">No Preview</div>
                        )}
                      </div>
                      <div className="p-2 bg-black/40">
                        <div className="text-[10px] font-semibold text-white/90 truncate capitalize">{(item.label || item.value).replace(/^.*[\/\\]/, '').replace(/\.png$/i, '').replace(/_/g, ' ')}</div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="h-full">
        <PreviewPanel originalUrl={uploadedUrl} previewUrl={previewUrl} onReset={handleReset} onDownload={handleDownload} />
      </section>

      {loading && <LoadingOverlay status={status} />}
    </div>
  )
}
