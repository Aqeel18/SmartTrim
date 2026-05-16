import React from 'react'
import { useTheme } from '../context/ThemeContext.jsx'

export default function Logo({ className = "w-10 h-10" }) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  
  // A sleek geometric "S" crossed by a sharp slicing diagonal line representing precision
  return (
    <svg 
      className={className} 
      viewBox="0 0 100 100" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
    >
      <g transform="translate(10, 10) scale(0.8)">
        {/* Outer sharp hexagon representing the mirror/face shape */}
        <path 
          d="M50 0L93.3013 25V75L50 100L6.69873 75V25L50 0Z" 
          stroke={isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)"} 
          strokeWidth="2"
        />
        
        {/* The Geometric S */}
        <path 
          d="M65 30C65 20 58 15 50 15C42 15 35 20 35 30C35 40 45 45 50 50C55 55 65 60 65 70C65 80 58 85 50 85C42 85 35 80 35 70" 
          stroke="url(#gradient-s)" 
          strokeWidth="10" 
          strokeLinecap="round" 
          strokeLinejoin="round"
        />
        
        {/* The Precision Slice / Razor Edge */}
        <path 
          d="M15 85L85 15" 
          stroke={isDark ? "#00e5ff" : "#0284c7"} 
          strokeWidth="6" 
          strokeLinecap="square"
          className="animate-pulse"
        />
        
        <defs>
          <linearGradient id="gradient-s" x1="35" y1="15" x2="65" y2="85" gradientUnits="userSpaceOnUse">
            <stop stopColor={isDark ? "#ffffff" : "#0f172a"} />
            <stop offset="1" stopColor={isDark ? "#9ca3af" : "#64748b"} />
          </linearGradient>
        </defs>
      </g>
    </svg>
  )
}
