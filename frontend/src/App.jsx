import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { AppProvider } from './context/AppContext.jsx'
import Navbar from './components/Navbar.jsx'
import Home from './pages/Home.jsx'
import UploadCapture from './pages/UploadCapture.jsx'
import AnalysisDashboard from './pages/AnalysisDashboard.jsx'
import Studio from './pages/Studio.jsx'
import History from './pages/History.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'
import TrimmerIntro from './components/TrimmerIntro.jsx'

function AnimatedRoutes() {
  const location = useLocation()
  return (
    <AnimatePresence mode="wait">
      <motion.div 
        key={location.pathname} 
        initial={{ opacity: 0, y: 15, filter: 'blur(10px)' }} 
        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }} 
        exit={{ opacity: 0, y: -15, filter: 'blur(10px)' }} 
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="w-full h-full"
      >
        <Routes location={location}>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<UploadCapture />} />
          <Route path="/analysis" element={<AnalysisDashboard />} />
          <Route path="/studio" element={<Studio />} />
          <Route path="/history" element={<History />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  )
}

export default function App() {
  const [introDone, setIntroDone] = useState(false)

  return (
    <ErrorBoundary>
      <AppProvider>
        <BrowserRouter>
          <div className="min-h-screen flex flex-col bg-background font-sans text-textMain overflow-x-hidden transition-colors duration-500">
            {/* Intro is a fixed overlay — routes render underneath so there's no blank flash */}
            <TrimmerIntro onComplete={() => setIntroDone(true)} />
            <Navbar />
            <main className="flex-1 relative w-full h-full flex flex-col">
              <AnimatedRoutes />
            </main>
          </div>
        </BrowserRouter>
      </AppProvider>
    </ErrorBoundary>
  )
}
