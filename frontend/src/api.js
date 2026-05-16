/**
 * SmartTrim 360 — API Client
 *
 * All backend communication is centralised here.
 * The async preview flow works as follows:
 *   1. submitPreviewJob()  → POST /preview-async  → { job_id }
 *   2. connectJobSocket()  → WS /ws/job/{id}      → progress events pushed server → client
 *   3. pollJobStatus()     → GET /jobs/{id}        → fallback if WebSocket unavailable
 */

const BASE = ''  // Vite proxy forwards all /api calls; nginx proxies /api → backend

// ─── Error helper ────────────────────────────────────────────────────────────

async function _handleResponse(resp) {
  if (resp.ok) return resp
  const text = await resp.text()
  try {
    const json = JSON.parse(text)
    throw new Error(json?.detail || `Server error ${resp.status}`)
  } catch (_) {
    throw new Error(text || `Server error ${resp.status}`)
  }
}

// ─── Hairstyle assets ─────────────────────────────────────────────────────────

export async function fetchHairstyles() {
  const resp = await fetch(`${BASE}/hairstyles`)
  await _handleResponse(resp)
  return resp.json()
}

// ─── Face analysis ────────────────────────────────────────────────────────────

export async function analyzeFaceShape(imageFile) {
  const form = new FormData()
  form.append('image', imageFile)
  const resp = await fetch(`${BASE}/analyze-face-shape`, { method: 'POST', body: form })
  await _handleResponse(resp)
  return resp.json()
}

// ─── CLIP semantic recommendations ───────────────────────────────────────────

/**
 * Get AI-ranked hairstyle recommendations using CLIP image embeddings.
 *
 * @param {File}   imageFile  User's face photo
 * @param {string} faceShape  e.g. 'Oval'
 * @returns {Promise<{face_shape: string, recommendations: Array}>}
 */
export async function fetchSemanticRecommendations(imageFile, faceShape) {
  const form = new FormData()
  form.append('image', imageFile)
  form.append('face_shape', faceShape)
  const resp = await fetch(`${BASE}/recommend`, { method: 'POST', body: form })
  await _handleResponse(resp)
  return resp.json()
}

// ─── Synchronous preview (fallback) ──────────────────────────────────────────

export async function generatePreview({ imageFile, hairstyle }) {
  const form = new FormData()
  form.append('image', imageFile)
  form.append('hairstyle', hairstyle)
  const resp = await fetch(`${BASE}/preview`, { method: 'POST', body: form })
  await _handleResponse(resp)
  return resp.blob()
}

// ─── Async preview — submit ───────────────────────────────────────────────────

/**
 * Submit an async generation job. Returns immediately with a job_id.
 *
 * @param {File}   imageFile
 * @param {string} hairstyle  Style value string
 * @returns {Promise<{job_id: string, status: string}>}
 */
export async function submitPreviewJob({ imageFile, hairstyle }) {
  const form = new FormData()
  form.append('image', imageFile)
  form.append('hairstyle', hairstyle)
  const resp = await fetch(`${BASE}/preview-async`, { method: 'POST', body: form })
  await _handleResponse(resp)
  return resp.json()
}

// ─── Async preview — poll ─────────────────────────────────────────────────────

/**
 * Poll a job's status. Returns the full job object.
 * When status === 'done', result contains a base64-encoded JPEG.
 */
export async function pollJobStatus(jobId) {
  const resp = await fetch(`${BASE}/jobs/${jobId}`)
  await _handleResponse(resp)
  return resp.json()
}

// ─── Async preview — WebSocket stream ────────────────────────────────────────

/**
 * Open a WebSocket connection that streams job progress in real time.
 *
 * @param {string}   jobId
 * @param {object}   callbacks
 * @param {Function} callbacks.onProgress  (job: object) => void
 * @param {Function} callbacks.onDone      (base64Jpeg: string) => void
 * @param {Function} callbacks.onError     (message: string) => void
 * @returns {WebSocket} — call .close() to disconnect early
 */
export function connectJobSocket(jobId, { onProgress, onDone, onError } = {}) {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host  = window.location.host
  const url   = `${proto}://${host}/ws/job/${jobId}`

  const ws = new WebSocket(url)

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.error) {
        onError?.(data.error)
        ws.close()
        return
      }

      onProgress?.(data)

      if (data.status === 'done') {
        onDone?.(data.result)    // base64 JPEG string
        ws.close()
      } else if (data.status === 'failed') {
        onError?.(data.error || 'Generation failed.')
        ws.close()
      }
    } catch (err) {
      onError?.('Failed to parse server message.')
    }
  }

  ws.onerror = () => onError?.('WebSocket connection error.')
  ws.onclose = () => {}

  return ws
}

// ─── Validation images (legacy) ───────────────────────────────────────────────

export async function fetchValidations() {
  const resp = await fetch(`${BASE}/validations`)
  await _handleResponse(resp)
  return resp.json()
}
