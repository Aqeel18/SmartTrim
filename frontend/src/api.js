// Thin API client for SmartTrim_360 frontend

export async function generatePreview({ imageFile, hairstyle }) {
  const form = new FormData()
  form.append('image', imageFile)
  form.append('hairstyle', hairstyle)

  // Use proxy to '/preview' to avoid CORS in dev
  const resp = await fetch('/preview', {
    method: 'POST',
    body: form,
  })

  if (!resp.ok) {
    // Try to extract server-provided error message
    const text = await resp.text()
    try {
      const json = JSON.parse(text)
      throw new Error(json?.detail || 'Server error')
    } catch (_) {
      throw new Error(text || 'Server error')
    }
  }

  const blob = await resp.blob()
  return blob
}

export async function fetchValidations() {
  const resp = await fetch('/validations')
  if (!resp.ok) {
    throw new Error('Failed to fetch validation images')
  }
  return await resp.json()
}

export async function fetchHairstyles() {
  const resp = await fetch('/hairstyles')
  if (!resp.ok) {
    throw new Error('Failed to fetch hairstyles')
  }
  return await resp.json()
}

export async function analyzeFaceShape(imageFile) {
  const form = new FormData()
  form.append('image', imageFile)

  const resp = await fetch('/analyze-face-shape', {
    method: 'POST',
    body: form,
  })
  if (!resp.ok) {
    const text = await resp.text()
    try {
      const json = JSON.parse(text)
      throw new Error(json?.detail || 'Analysis error')
    } catch (_) {
      throw new Error(text || 'Analysis error')
    }
  }
  return await resp.json()
}
