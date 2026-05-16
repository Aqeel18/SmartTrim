import React, { useCallback, useRef } from 'react'
import styles from '../styles/UploadArea.module.css'

export default function UploadArea({ onFileSelected, previewUrl, showPreview = true }) {
  const inputRef = useRef(null)

  const onInputChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return onFileSelected(null)
    const okTypes = ['image/jpeg', 'image/png']
    if (!okTypes.includes(file.type)) {
      alert('Please upload a JPG or PNG image.')
      return onFileSelected(null)
    }
    onFileSelected(file)
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    const file = e.dataTransfer.files?.[0]
    if (!file) return
    const okTypes = ['image/jpeg', 'image/png']
    if (!okTypes.includes(file.type)) {
      alert('Please upload a JPG or PNG image.')
      return onFileSelected(null)
    }
    onFileSelected(file)
  }, [onFileSelected])

  const onDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  return (
    <div>
      <div className={styles.dropzone} onDrop={onDrop} onDragOver={onDragOver}>
        {previewUrl && showPreview ? (
          <img src={previewUrl} alt="Uploaded preview" className={styles.preview} />
        ) : (
          <div className={styles.placeholder}>Drag & drop an image here, or click to select</div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png"
          className={styles.input}
          onChange={onInputChange}
          onClick={(e) => {
            // clicking dropzone triggers input via CSS overlay
          }}
        />
      </div>
    </div>
  )
}
