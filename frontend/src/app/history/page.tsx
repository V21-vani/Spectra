'use client'
import { useCallback, useEffect, useState } from 'react'
import { Save, Upload, Trash2, Clock } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { TestSession } from '@/lib/types'
import GlowCard from '@/components/GlowCard'

export default function HistoryPage() {
  const router = useRouter()
  const [sessions, setSessions] = useState<TestSession[]>([])
  const [name,     setName]     = useState('')
  const [saving,   setSaving]   = useState(false)

  const load = useCallback(() => api.getSessions().then(setSessions).catch(console.error), [])
  useEffect(() => { load() }, [load])

  async function save() {
    if (saving) return
    setSaving(true)
    const n = name.trim() || `Session ${new Date().toLocaleString()}`
    await api.saveSession(n).catch(console.error)
    setName('')
    load()
    setSaving(false)
  }

  async function loadSession(filename: string) {
    await api.loadSession(filename).catch(console.error)
    router.push('/results')
  }

  async function del(filename: string) {
    await api.deleteSession(filename).catch(console.error)
    load()
  }

  return (
    <div className="p-8 space-y-5">
      <h1 className="text-2xl font-bold font-mono tracking-widest text-[#e2e8f0]">
        <span className="text-cyan opacity-60 mr-2">&gt;</span>HISTORY
      </h1>

      {/* Save form */}
      <GlowCard title="ARCHIVE CURRENT RESULTS">
        <div className="flex gap-3">
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && save()}
            placeholder="Session name  (e.g. Sprint 14 — auth regression)"
            className="cyber-input flex-1"
          />
          <button onClick={save} disabled={saving} className="cyber-btn cyber-btn-primary flex items-center gap-2">
            <Save size={12} />
            {saving ? 'SAVING…' : 'SAVE'}
          </button>
        </div>
      </GlowCard>

      {/* Sessions */}
      {sessions.length === 0 ? (
        <GlowCard>
          <div className="py-10 text-center text-[#2d3058] font-mono text-xs tracking-widest">
            NO SESSIONS SAVED YET
          </div>
        </GlowCard>
      ) : (
        <div className="space-y-3">
          {sessions.map(s => {
            const res    = s.results ?? []
            const total  = res.length
            const passed = res.filter(r => r.status === 'PASSED').length
            const failed = res.filter(r => r.status === 'FAILED').length
            const rate   = total ? (passed / total * 100) : 0
            const rateColor = rate === 100 ? '#00ff88' : rate < 50 ? '#ff2d55' : '#ffb800'
            const ts = new Date(s.timestamp * 1000).toLocaleString()

            return (
              <GlowCard key={s._file}>
                <div className="flex items-center gap-5">
                  <div className="flex-1 min-w-0">
                    <div className="font-mono font-semibold text-sm text-[#e2e8f0] truncate">{s.name}</div>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <Clock size={10} className="text-[#2d3058]" />
                      <span className="text-[10px] font-mono text-[#2d3058]">{ts}</span>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-5 text-xs font-mono shrink-0">
                    <span className="text-[#4a5568]">{total} tests</span>
                    <span className="text-[#00ff88]">{passed} passed</span>
                    <span style={{ color: failed ? '#ff2d55' : '#2d3058' }}>{failed} failed</span>
                    <span className="text-lg font-bold" style={{ color: rateColor }}>
                      {total ? `${rate.toFixed(0)}%` : '—'}
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <button onClick={() => loadSession(s._file)} className="cyber-btn cyber-btn-primary flex items-center gap-1.5">
                      <Upload size={11} />LOAD
                    </button>
                    <button onClick={() => del(s._file)} className="cyber-btn cyber-btn-red flex items-center gap-1.5">
                      <Trash2 size={11} />
                    </button>
                  </div>
                </div>
              </GlowCard>
            )
          })}
        </div>
      )}
    </div>
  )
}
