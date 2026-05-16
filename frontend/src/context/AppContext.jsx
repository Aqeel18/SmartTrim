import React, { createContext, useContext, useState } from 'react'

const AppContext = createContext()

export function AppProvider({ children }) {
  // Global state across the funnel
  const [uploadedImage, setUploadedImage] = useState(null) // File or Blob
  const [uploadedUrl, setUploadedUrl] = useState(null)     // Object URL
  const [faceShapeResult, setFaceShapeResult] = useState(null)
  const [recommendedStyles, setRecommendedStyles] = useState([])
  const [history, setHistory] = useState([])
  const [allStyles, setAllStyles] = useState([])

  const saveToHistory = (item) => {
    setHistory(prev => {
      const next = [item, ...prev].slice(0, 20) // Keep last 20 in session
      return next
    })
  }

  const resetFlow = () => {
    setUploadedImage(null)
    setUploadedUrl(null)
    setFaceShapeResult(null)
    setRecommendedStyles([])
  }

  return (
    <AppContext.Provider value={{
      uploadedImage, setUploadedImage,
      uploadedUrl, setUploadedUrl,
      faceShapeResult, setFaceShapeResult,
      recommendedStyles, setRecommendedStyles,
      allStyles, setAllStyles,
      history, saveToHistory,
      resetFlow
    }}>
      {children}
    </AppContext.Provider>
  )
}

export function useAppContext() {
  return useContext(AppContext)
}
