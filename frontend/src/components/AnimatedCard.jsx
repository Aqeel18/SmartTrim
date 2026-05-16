import React, { useRef } from 'react'
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'
import { SparklesIcon } from '@heroicons/react/24/solid'

export default function AnimatedCard({ styleInfo, onSelect, selected, isRecommended }) {
  const isSelected = selected === styleInfo.value
  const ref = useRef(null)

  const x = useMotionValue(0)
  const y = useMotionValue(0)

  const mouseXSpring = useSpring(x, { stiffness: 300, damping: 40 })
  const mouseYSpring = useSpring(y, { stiffness: 300, damping: 40 })

  const rotateX = useTransform(mouseYSpring, [-0.5, 0.5], ["10deg", "-10deg"])
  const rotateY = useTransform(mouseXSpring, [-0.5, 0.5], ["-10deg", "10deg"])

  const handleMouseMove = (e) => {
    const rect = ref.current.getBoundingClientRect()
    const width = rect.width
    const height = rect.height
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    const xPct = mouseX / width - 0.5
    const yPct = mouseY / height - 0.5
    x.set(xPct)
    y.set(yPct)
  }

  const handleMouseLeave = () => {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={() => onSelect(styleInfo.value)}
      className={`relative rounded-2xl cursor-pointer group
        ${isSelected ? 'shadow-[0_0_20px_var(--primary-glow-start)]' : 'shadow-lg'}
      `}
    >
      <div 
        className={`aspect-[4/5] bg-surfaceHighlight rounded-2xl overflow-hidden relative border transition-all duration-300
        ${isSelected ? 'border-primary ring-1 ring-primary' : 'border-textMain/10 group-hover:border-primary/50'}`}
        style={{ transform: "translateZ(30px)" }}
      >
        <img 
          src={styleInfo.image_url} 
          alt={styleInfo.name || styleInfo.value} 
          className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110 opacity-80 group-hover:opacity-100"
          loading="lazy"
        />
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent opacity-80 group-hover:opacity-90 transition-opacity" />
        
        {/* Recommended Badge */}
        {isRecommended && (
          <div className="absolute top-3 left-3 bg-primary/90 backdrop-blur-md text-black px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest flex items-center gap-1.5 shadow-lg" style={{ transform: "translateZ(50px)" }}>
            <SparklesIcon className="w-3 h-3" />
            Matching
          </div>
        )}

        {isSelected && (
          <div className="absolute top-3 right-3 bg-primary text-black p-1.5 rounded-full shadow-[0_0_10px_var(--primary-glow-end)]" style={{ transform: "translateZ(50px)" }}>
            <SparklesIcon className="w-4 h-4" />
          </div>
        )}

        <div className="absolute bottom-0 left-0 right-0 p-4" style={{ transform: "translateZ(40px)" }}>
          <p className="text-[10px] text-primary font-display font-bold tracking-widest uppercase mb-1 drop-shadow-md">
            {styleInfo.category || 'Premium Style'}
          </p>
          <h4 className="text-white font-sans font-semibold text-base md:text-lg drop-shadow-md leading-tight capitalize">
            {(styleInfo.name || styleInfo.value).replace(/^.*[\/\\]/, '').replace(/\.png$/i, '').replace(/_/g, ' ')}
          </h4>
        </div>
      </div>
    </motion.div>
  )
}
