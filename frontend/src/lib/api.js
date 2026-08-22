/**
 * API client for the DocMind AI backend.
 *
 * WHY ALL FETCH CALLS LIVE IN THIS ONE FILE:
 * Every component that needs data calls a function from here, never
 * `fetch()` directly. That means the base URL, error handling, and
 * JSON parsing logic exist in exactly one place - if the backend's
 * base URL changes (e.g. deploying somewhere other than localhost),
 * or if we want to add auth headers later, it's a one-file change,
 * not a hunt through every component.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

class ApiError extends Error {
  constructor(message, status, detail) {
    super(message)
    this.status = status
    this.detail = detail
  }
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options)
  if (!res.ok) {
    // FastAPI's HTTPException responses put the real message in
    // `detail` - surfacing that (not just "Request failed") is what
    // let us actually debug the backend during development, so the
    // frontend should get the same courtesy.
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      // response wasn't JSON - fall back to statusText, already set
    }
    throw new ApiError(`API error (${res.status})`, res.status, detail)
  }
  return res.json()
}

export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request('/upload', { method: 'POST', body: formData })
}

export async function getDocumentStatus(fileId) {
  return request(`/documents/${fileId}/status`)
}

export async function listDocuments() {
  return request('/documents')
}

export async function queryDocument(fileId, question) {
  return request('/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id: fileId, question }),
  })
}

export async function getMetrics() {
  return request('/metrics')
}

export { ApiError }
