import React from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '../context/ThemeContext.jsx'

export default function Home() {
  const navigate = useNavigate()
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [currentImageIndex, setCurrentImageIndex] = React.useState(0)

  React.useEffect(() => {
    const timer = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % 4)
    }, 4000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="relative flex-1 flex items-center justify-center overflow-hidden min-h-screen pt-12">
      {/* Background Image & Overlay */}
      <motion.div 
        initial={{ scale: 1.1, opacity: 0 }}
        animate={{ scale: 1, opacity: isDark ? 0.6 : 0.3 }}
        transition={{ duration: 2, ease: "easeOut" }}
        className="absolute inset-0 z-0"
      >
        <img 
          src="/hero-bg-v3.png" 
          alt="Premium Studio" 
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/80 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-background via-transparent to-background/50" />
      </motion.div>

      {/* Hero Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 w-full flex flex-col md:flex-row items-center justify-between">
        
        <div className="max-w-3xl w-full">
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
          >
            <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full border border-textMain/10 backdrop-blur-md mb-8 bg-surface/30">
              <span className="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_var(--primary)] animate-pulse"></span>
              <span className="text-xs font-bold text-textMain tracking-[0.2em] uppercase">The Future of Grooming</span>
            </div>
            
            <h1 className="text-6xl md:text-8xl font-display font-bold tracking-tighter text-textMain mb-6 leading-[0.95]">
              Precision.<br/>
              <span className="text-gradient">Perfected.</span>
            </h1>
            
            <p className="text-lg md:text-xl text-textMuted mb-12 leading-relaxed max-w-xl font-light">
              Experience the world's most advanced AI grooming assistant. 
              Analyze your facial geometry and discover the styles tailored exclusively for your proportions.
            </p>

            <div className="flex flex-col sm:flex-row gap-6">
              <button 
                onClick={() => navigate('/upload')}
                className="group relative inline-flex items-center justify-center gap-4 px-10 py-5 bg-primary text-black font-bold rounded-full overflow-hidden transition-all duration-300 hover:scale-[1.02] shadow-[0_0_20px_var(--primary-glow-start)] hover:shadow-[0_0_30px_var(--primary-glow-end)]"
              >
                <span className="relative z-10 font-display tracking-wide uppercase text-sm">Start Analysis</span>
                <svg className="w-5 h-5 relative z-10 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/30 to-white/0 -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
              </button>
              
              <button 
                onClick={() => navigate('/history')}
                className="inline-flex items-center justify-center px-8 py-5 rounded-full border border-textMain/20 text-textMain font-display font-bold tracking-wide uppercase text-sm hover:bg-surfaceHighlight transition-colors"
              >
                View History
              </button>
            </div>
          </motion.div>
        </div>
        
        {/* Decorative Graphic Element (Style Showcase) */}
        <motion.div 
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1, ease: "easeOut", delay: 0.5 }}
          className="hidden lg:block w-[400px] h-[500px] relative"
        >
          <div className="absolute inset-0 border border-textMain/10 rounded-[2rem] backdrop-blur-md bg-surface/5 flex flex-col items-center justify-center overflow-hidden group">
             {/* Animated scanning line */}
             <motion.div 
               animate={{ top: ['0%', '100%', '0%'] }}
               transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
               className="absolute left-0 right-0 h-1 bg-primary/40 z-30 shadow-[0_0_30px_var(--primary)]" 
             />
             
             {/* Slideshow Container */}
             <div className="absolute inset-0 z-10">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={currentImageIndex}
                    initial={{ opacity: 0, scale: 1.1 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 1.5, ease: "easeInOut" }}
                    className="absolute inset-0"
                  >
                    <img 
                      src={[
                        '/ui-assets/uiimage.webp',
                        '/ui-assets/uiimage2.webp',
                        '/ui-assets/uiimage3.jpeg',
                        '/ui-assets/uiimage4.jpg'
                      ][currentImageIndex]} 
                      alt="Style Preview" 
                      className="w-full h-full object-cover transition-all duration-1000 group-hover:scale-105" 
                    />
                    {/* Soft gradient to ensure text readability without heavy black bars */}
                    <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-transparent to-background/20" />
                  </motion.div>
                </AnimatePresence>
             </div>

             {/* UI Overlay Elements */}
             <div className="absolute top-6 left-6 z-20 flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary animate-ping" />
                <span className="text-[10px] font-bold text-textMain tracking-widest uppercase opacity-70">Live Synthesis</span>
             </div>

             <div className="absolute bottom-10 left-0 right-0 text-center z-30 px-8">
               <motion.div 
                 initial={{ y: 20, opacity: 0 }}
                 animate={{ y: 0, opacity: 1 }}
                 className="space-y-1"
               >
                 <div className="text-5xl font-display font-bold text-primary tracking-tighter drop-shadow-[0_0_20px_rgba(0,229,255,0.5)]">
                   360°
                 </div>
                 <div className="text-[11px] text-textMain uppercase tracking-[0.4em] font-bold opacity-80">Precision Matrix</div>
               </motion.div>
             </div>
             
             {/* Decorative Corner Accents */}
             <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-primary/40" />
             <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-primary/40" />
          </div>
        </motion.div>

      </div>
    </div>
  )
}
