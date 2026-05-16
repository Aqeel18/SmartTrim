import React, { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { Bars3Icon, XMarkIcon, SunIcon, MoonIcon } from '@heroicons/react/24/outline'
import Logo from './Logo.jsx'
import { useTheme } from '../context/ThemeContext.jsx'

const linkBase = 'px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300'
const linkActive = 'text-primary bg-primary/10 shadow-[0_0_15px_var(--primary-glow-start)]'
const linkInactive = 'text-textMuted hover:text-textMain hover:bg-surfaceHighlight'

export default function Navbar() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'
  
  if (location.pathname === '/studio') return null

  const linkClass = ({ isActive }) => `${linkBase} ${isActive ? linkActive : linkInactive}`

  return (
    <nav className="fixed top-0 w-full z-40 bg-surface/80 backdrop-blur-xl border-b border-textMain/5 transition-colors duration-500">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3 cursor-pointer group">
          <Logo className="w-10 h-10 group-hover:scale-110 transition-transform" />
          <div className="text-xl font-display font-bold tracking-widest text-textMain uppercase">
            SmartTrim<span className="text-primary font-light">360</span>
          </div>
        </div>
        
        <div className="hidden md:flex items-center gap-6">
          <NavLink to="/" className={linkClass}>Home</NavLink>
          <NavLink to="/upload" className={linkClass}>Analysis</NavLink>
          {location.pathname !== '/' && (
            <NavLink to="/studio" className={linkClass}>Try-On Studio</NavLink>
          )}
          
          {/* Theme Toggle */}
          <button 
            onClick={toggleTheme} 
            className="p-2 rounded-full border border-textMain/10 text-textMuted hover:text-primary hover:border-primary transition-all shadow-sm"
          >
            {isDark ? <SunIcon className="w-5 h-5" /> : <MoonIcon className="w-5 h-5" />}
          </button>
        </div>
        
        <button className="md:hidden text-textMain hover:text-primary transition" onClick={() => setOpen((v) => !v)}>
          {open ? <XMarkIcon className="w-7 h-7" /> : <Bars3Icon className="w-7 h-7" />}
        </button>
      </div>

      {open && (
        <div className="md:hidden bg-surface/95 backdrop-blur-3xl border-b border-textMain/10 px-6 py-4 flex flex-col gap-3 animate-fade-in shadow-2xl">
          <NavLink to="/" onClick={() => setOpen(false)} className={linkClass}>Home</NavLink>
          <NavLink to="/upload" onClick={() => setOpen(false)} className={linkClass}>Analysis</NavLink>
          <NavLink to="/history" onClick={() => setOpen(false)} className={linkClass}>History</NavLink>
          <button 
            onClick={() => { toggleTheme(); setOpen(false); }} 
            className="flex items-center gap-3 px-4 py-2 mt-2 border border-textMain/10 rounded-lg text-sm font-semibold text-textMuted"
          >
            {isDark ? <SunIcon className="w-5 h-5" /> : <MoonIcon className="w-5 h-5" />}
            Toggle Theme
          </button>
        </div>
      )}
    </nav>
  )
}
