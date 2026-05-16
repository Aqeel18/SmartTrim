import React from 'react'

export default function About() {
  return (
    <div className="prose prose-invert max-w-none">
      <h2>About SmartTrim 360</h2>
      <p>
        SmartTrim 360 lets you preview hairstyles realistically using AI-driven hair matting, face-shape analysis, and geometry-aware blending.
        The experience is fast, simple, and privacy‑respecting.
      </p>
      <h3>What It Does</h3>
      <ul>
        <li>Recommends styles based on detected face shape.</li>
        <li>Uses high‑quality, cleaned assets with transparent alpha.</li>
        <li>Generates natural try‑ons with lighting‑aware compositing.</li>
      </ul>
      <h3>How It Works</h3>
      <ul>
        <li>Face geometry is analyzed locally-initiated via our secure API.</li>
        <li>MODNet powers hair matting for clean, 4‑channel PNGs.</li>
        <li>Warping aligns styles to your photo for a realistic preview.</li>
      </ul>
      <h3>Privacy & Safety</h3>
      <ul>
        <li>Your uploads are used only to generate previews during the session.</li>
        <li>No public gallery: your results remain private to you.</li>
      </ul>
      <p>
        Questions or feedback? Let us know which styles you’d like to see next.
      </p>
    </div>
  )
}
