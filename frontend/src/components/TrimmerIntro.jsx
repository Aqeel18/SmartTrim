import React, { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence, useMotionValue, animate, useMotionValueEvent } from 'framer-motion'

// ── Session guard ─────────────────────────────────────────────────────────────
function introAlreadyPlayed() {
  return typeof window !== 'undefined' && !!window.__smarttrimIntroPlayed
}

// ── Trimmer SVG ───────────────────────────────────────────────────────────────
// Blade tip is at x=0 (left edge of SVG) — used for sync math below
const BLADE_TIP_OFFSET = 0   // how far the blade tip is from the SVG origin
const TRIMMER_W = 160

function TrimmerSVG() {
  return (
    <svg width={TRIMMER_W} height="60" viewBox="0 0 160 60" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* ── Body ── */}
      <rect x="2" y="2" width="140" height="38" rx="12" fill="#0a0a0a" stroke="var(--primary)" strokeWidth="1.5"/>
      {/* Top sheen */}
      <rect x="14" y="9" width="116" height="5" rx="2.5" fill="var(--primary)" opacity="0.1"/>
      {/* Grip ridges */}
      {[28, 42, 56, 70].map(x => (
        <rect key={x} x={x} y="13" width="5" height="20" rx="2.5" fill="var(--primary)" opacity="0.28"/>
      ))}
      {/* Power button */}
      <circle cx="128" cy="21" r="9" fill="var(--primary)" opacity="0.08" stroke="var(--primary)" strokeWidth="1.2"/>
      <circle cx="128" cy="21" r="4.5" fill="var(--primary)"/>
      <rect x="126.5" y="14.5" width="3" height="8" rx="1.5" fill="#000" opacity="0.5"/>
      {/* ── Blade plate ── */}
      <rect x="0" y="38" width="158" height="10" rx="4" fill="var(--primary)" opacity="0.85"/>
      {/* Blade teeth */}
      {Array.from({ length: 20 }, (_, i) => (
        <rect key={i} x={i * 8 + 1} y="46" width="5.5" height="14" rx="1.5" fill="var(--primary)"/>
      ))}
      {/* Blade glow highlight */}
      <rect x="0" y="38" width="158" height="3.5" rx="1.5" fill="white" opacity="0.55"/>
      {/* Leading edge glow */}
      <rect x="152" y="38" width="8" height="22" rx="2" fill="white" opacity="0.3"/>
    </svg>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function TrimmerIntro({ onComplete }) {
  const [show, setShow]         = useState(false)
  const [shouldPlay]            = useState(() => !introAlreadyPlayed())
  const textRef                 = useRef(null)

  // Single motion value drives both trimmer position AND text mask — perfect sync
  const trimmerX = useMotionValue(-TRIMMER_W - 20)

  // On every frame, update a CSS variable on the text so the mask follows the blade tip exactly
  useMotionValueEvent(trimmerX, 'change', (latest) => {
    if (!textRef.current) return
    const rect    = textRef.current.getBoundingClientRect()
    const bladeTip = latest + BLADE_TIP_OFFSET + TRIMMER_W  // right edge of blade
    const rel      = Math.max(0, Math.min(rect.width, bladeTip - rect.left))
    textRef.current.style.setProperty('--reveal-x', `${rel}px`)
  })

  useEffect(() => {
    if (!shouldPlay) { onComplete(); return }
    window.__smarttrimIntroPlayed = true
    setShow(true)

    const vw = window.innerWidth
    const controls = animate(trimmerX, vw + TRIMMER_W + 20, {
      duration: 2.6,
      ease: [0.18, 0, 0.28, 1],
      delay: 0.5,
    })

    const dismiss = setTimeout(() => {
      setShow(false)
      setTimeout(onComplete, 750)
    }, 3900)

    return () => { controls.stop(); clearTimeout(dismiss) }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (!shouldPlay) return null

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          key="intro"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.75, ease: 'easeInOut' }}
          style={{
            position: 'fixed', inset: 0, zIndex: 9999,
            // Always pure black — intro is cinematic regardless of theme
            backgroundColor: '#020810',
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            overflow: 'hidden',
          }}
        >
          {/* Vignette */}
          <div style={{
            position: 'absolute', inset: 0, pointerEvents: 'none',
            background: 'radial-gradient(ellipse at center, transparent 35%, rgba(0,0,0,0.88) 100%)',
          }} />

          {/* Subtle grid */}
          <div style={{
            position: 'absolute', inset: 0, pointerEvents: 'none',
            backgroundImage: `linear-gradient(var(--primary) 1px, transparent 1px),
                              linear-gradient(90deg, var(--primary) 1px, transparent 1px)`,
            backgroundSize: '72px 72px',
            opacity: 0.022,
          }} />

          {/* ── Trimmer (moved by motion value) ── */}
          <motion.div
            style={{
              position: 'absolute',
              top: 'calc(50% - 80px)',
              left: 0,
              x: trimmerX,
              zIndex: 30,
              filter: 'drop-shadow(0 0 22px var(--primary)) drop-shadow(0 6px 14px rgba(0,0,0,0.9))',
              willChange: 'transform',
            }}
          >
            <TrimmerSVG />
          </motion.div>

          {/* Blade-tip spark (follows exact same x as trimmer + blade width) */}
          <motion.div
            style={{
              position: 'absolute',
              top: 'calc(50% - 14px)',
              left: `${TRIMMER_W}px`,
              x: trimmerX,
              width: '4px',
              height: '28px',
              borderRadius: '2px',
              background: 'white',
              boxShadow: '0 0 18px 8px var(--primary), 0 0 40px 16px rgba(0,229,255,0.25)',
              zIndex: 31,
              willChange: 'transform',
            }}
          />

          {/* ── Text — mask follows blade in real-time ── */}
          <div
            ref={textRef}
            style={{
              position: 'relative',
              zIndex: 10,
              textAlign: 'center',
              // CSS mask driven by --reveal-x (updated per frame in useMotionValueEvent)
              WebkitMaskImage: 'linear-gradient(90deg, #fff 0px, #fff var(--reveal-x, 0px), transparent var(--reveal-x, 0px))',
              maskImage:       'linear-gradient(90deg, #fff 0px, #fff var(--reveal-x, 0px), transparent var(--reveal-x, 0px))',
              '--reveal-x': '0px',
            }}
          >
            {/* Main wordmark */}
            <div style={{ lineHeight: 1, userSelect: 'none' }}>

              {/* SMART — wide tracked label */}
              <div style={{
                fontFamily: '"Outfit", "Inter", system-ui, sans-serif',
                fontSize: 'clamp(0.75rem, 2.2vw, 1.4rem)',
                fontWeight: 400,
                letterSpacing: '0.65em',
                textTransform: 'uppercase',
                // Solid visible color — no transparency
                color: 'rgba(0, 229, 255, 0.7)',
                marginBottom: '0.15em',
                paddingLeft: '0.65em',
              }}>
                Smart
              </div>

              {/* TRIM — hero word: SOLID white, no gradient-clip (breaks under mask) */}
              <div style={{
                fontFamily: '"Outfit", "Inter", system-ui, sans-serif',
                fontSize: 'clamp(4.5rem, 15vw, 11rem)',
                fontWeight: 900,
                letterSpacing: '-0.035em',
                lineHeight: 0.88,
                textTransform: 'uppercase',
                // Pure white — maximum contrast on black
                color: '#ffffff',
                // Layered neon glow (textShadow works correctly unlike gradient-clip under mask)
                textShadow: [
                  '0 0 30px rgba(0,229,255,0.9)',
                  '0 0 60px rgba(0,229,255,0.5)',
                  '0 0 100px rgba(0,229,255,0.25)',
                  '0 2px 0 rgba(0,0,0,0.8)',
                ].join(', '),
              }}>
                TRIM
              </div>

              {/* 360 — neon accent */}
              <div style={{
                fontFamily: '"Outfit", "Inter", system-ui, sans-serif',
                fontSize: 'clamp(1rem, 3.5vw, 2.2rem)',
                fontWeight: 300,
                letterSpacing: '0.8em',
                paddingLeft: '0.8em',
                // Solid primary color — no transparency
                color: '#00e5ff',
                lineHeight: 1.2,
                textShadow: '0 0 20px rgba(0,229,255,0.8), 0 0 40px rgba(0,229,255,0.4)',
              }}>
                360
              </div>
            </div>

            {/* Tagline — fades in after sweep, not part of the mask */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, delay: 3.2 }}
              style={{
                marginTop: '2rem',
                fontFamily: '"Outfit", system-ui, sans-serif',
                fontSize: 'clamp(0.55rem, 1.2vw, 0.7rem)',
                fontWeight: 600,
                letterSpacing: '0.55em',
                textTransform: 'uppercase',
                color: 'var(--text-muted)',
                paddingLeft: '0.55em',
                WebkitMaskImage: 'none',
                maskImage: 'none',
              }}
            >
              AI Grooming · Precision Engineered
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
