import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, useAnimation } from 'framer-motion'
import { useAppContext } from '../context/AppContext.jsx'
import { ArrowUpTrayIcon, CameraIcon } from '@heroicons/react/24/outline'

export default function UploadCapture() {
  const navigate = useNavigate()
  const { setUploadedImage, setUploadedUrl, resetFlow } = useAppContext()
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef(null)
  const controls = useAnimation()

  const handleFile = (file) => {
    if (file && file.type.startsWith('image/')) {
      resetFlow()
      setUploadedImage(file)
      setUploadedUrl(URL.createObjectURL(file))
      navigate('/analysis')
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    controls.start({ scale: 1 })
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    if (!isDragging) {
      setIsDragging(true)
      controls.start({ scale: 1.05 })
    }
  }

  const handleDragLeave = () => {
    setIsDragging(false)
    controls.start({ scale: 1 })
  }

  return (
    <div className="min-h-screen pt-32 pb-12 px-6 flex flex-col items-center relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--surface-highlight),_transparent_70%)] opacity-30 pointer-events-none" />
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="text-center mb-12 z-10"
      >
        <h2 className="text-4xl md:text-5xl font-display font-bold text-textMain mb-4">Initialize Analysis</h2>
        <p className="text-textMuted max-w-lg mx-auto">
          Upload a high-quality portrait for precision facial mapping. Ensure adequate lighting and remove accessories.
        </p>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="w-full max-w-2xl relative z-10"
      >
        <motion.div 
          animate={controls}
          className="glass-panel rounded-[2rem] p-4 relative overflow-hidden group cursor-pointer"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          {/* Animated Glow Border on Drag */}
          {isDragging && <div className="absolute inset-0 bg-primary/10 rounded-[2rem] animate-pulse pointer-events-none" />}

          <div className={`border-2 border-dashed rounded-[1.5rem] p-16 transition-all duration-300 flex flex-col items-center justify-center text-center min-h-[400px] relative overflow-hidden
            ${isDragging ? 'border-primary' : 'border-textMain/20 group-hover:border-primary/50'}`}>
            
            {/* Background elements */}
            <div className="absolute inset-0 bg-surface/30 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="absolute -top-32 -right-32 w-64 h-64 bg-primary/10 rounded-full blur-3xl group-hover:bg-primary/20 transition-colors duration-500" />
            <div className="absolute -bottom-32 -left-32 w-64 h-64 bg-accent/5 rounded-full blur-3xl group-hover:bg-accent/10 transition-colors duration-500" />

            {/* Icon */}
            <motion.div 
              animate={{ y: isDragging ? -10 : 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
              className={`w-24 h-24 rounded-full flex items-center justify-center mb-8 relative z-10 transition-colors duration-300
                ${isDragging ? 'bg-primary text-background shadow-[0_0_30px_var(--primary-glow-end)]' : 'bg-surfaceHighlight text-primary shadow-[0_0_15px_rgba(0,0,0,0.1)] group-hover:bg-primary/20'}`}
            >
              <ArrowUpTrayIcon className="w-10 h-10" />
            </motion.div>

            <h3 className="text-2xl font-bold text-textMain mb-2 relative z-10">
              {isDragging ? 'Drop to scan geometry' : 'Select or drop image'}
            </h3>
            <p className="text-sm text-textMuted mb-8 relative z-10">JPG, PNG, WEBP • Max 10MB</p>
            
            <input 
              type="file" 
              accept="image/jpeg, image/png, image/webp" 
              className="hidden" 
              ref={fileInputRef}
              onChange={(e) => handleFile(e.target.files[0])}
            />
            
            <div className="flex flex-col items-center gap-4 relative z-10">
              <button 
                className="px-10 py-4 bg-primary text-black font-bold rounded-full hover:scale-105 transition-all shadow-[0_0_30px_var(--primary-glow-start)] uppercase text-xs tracking-widest"
                onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click() }}
              >
                Browse Files
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}
