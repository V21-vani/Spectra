import { TestResult, TestSession } from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
export const WS_BASE = BASE.replace(/^http/, 'ws')

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'Request failed')
  }
  // 204 No Content
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  // Results
  getResults: ()                   => req<TestResult[]>('/api/results'),
  addResult:  (data: Partial<TestResult>) =>
    req<TestResult>('/api/results', { method: 'POST', body: JSON.stringify(data) }),
  deleteResult: (id: string)       => req<void>(`/api/results/${id}`, { method: 'DELETE' }),
  clearResults: ()                 => req<void>('/api/results', { method: 'DELETE' }),

  // Import
  importXml: (file: File) => {
    const form = new FormData(); form.append('file', file)
    return fetch(`${BASE}/api/import/xml`, { method: 'POST', body: form }).then(r => {
      if (!r.ok) return r.json().then(e => Promise.reject(new Error(e.detail)))
      return r.json() as Promise<TestResult[]>
    })
  },
  importJson: (file: File) => {
    const form = new FormData(); form.append('file', file)
    return fetch(`${BASE}/api/import/json`, { method: 'POST', body: form }).then(r => {
      if (!r.ok) return r.json().then(e => Promise.reject(new Error(e.detail)))
      return r.json() as Promise<TestResult[]>
    })
  },

  // Export — just open the URL
  exportCsvUrl:  () => `${BASE}/api/export/csv`,
  exportJsonUrl: () => `${BASE}/api/export/json`,

  // Sessions
  getSessions:   ()               => req<TestSession[]>('/api/sessions'),
  saveSession:   (name: string)   =>
    req<void>('/api/sessions', { method: 'POST', body: JSON.stringify({ name }) }),
  deleteSession: (filename: string) =>
    req<void>(`/api/sessions/${encodeURIComponent(filename)}`, { method: 'DELETE' }),
  loadSession:   (filename: string) =>
    req<TestResult[]>(`/api/sessions/${encodeURIComponent(filename)}/load`, { method: 'POST' }),
}
