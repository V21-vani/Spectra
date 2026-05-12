'use client'
import { useEffect, useRef, useState } from 'react'
import { FolderOpen, Play, Square, Upload, CheckCircle2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { WS_BASE } from '@/lib/api'
import GlowCard from '@/components/GlowCard'

type RunState = 'idle' | 'running' | 'done' | 'error'

function lineColor(line: string): string {
  const l = line.toLowerCase()
  if (l.includes('passed') && !l.includes('failed'))  return '#00ff88'
  if (l.includes('failed') || l.includes('error'))    return '#ff2d55'
  if (l.includes('warning') || l.includes('skipped')) return '#ffb800'
  if (l.startsWith('=') || l.startsWith('-'))          return '#00d4ff'
  if (l.startsWith('collected') || l.startsWith('platform')) return '#8b5cf6'
  return '#7db87d'
}

export default function RunPage() {
  const router = useRouter()
  const [path,     setPath]     = useState('')
  const [coverage, setCoverage] = useState(false)
  const [output,   setOutput]   = useState<string[]>([])
  const [runState, setRunState] = useState<RunState>('idle')
  const [summary,  setSummary]  = useState('')
  const termRef = useRef<HTMLDivElement>(null)
  const wsRef   = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (termRef.current) {
      termRef.current.scrollTop = termRef.current.scrollHeight
    }
  }, [output])

  function stop() {
    wsRef.current?.close()
    setRunState('idle')
  }

  function run() {
    const p = path.trim()
    if (!p) return
    setOutput([])
    setSummary('')
    setRunState('running')

    const ws = new WebSocket(`${WS_BASE}/ws/run`)
    wsRef.current = ws

    ws.onopen = () => ws.send(JSON.stringify({ path: p, coverage }))

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'line') {
        setOutput(prev => [...prev, msg.text])
      } else if (msg.type === 'done') {
        const results = msg.results ?? []
        const p2 = results.filter((r: any) => r.status === 'PASSED').length
        const f2 = results.filter((r: any) => r.status === 'FAILED').length
        const cNote = coverage && results.some((r: any) => r.coverage > 0)
          ? ` · avg cov ${(results.reduce((s: number, r: any) => s + r.coverage, 0) / results.length).toFixed(1)}%`
          : ''
        setSummary(msg.error ? `⚠ ${msg.error}` : `✓ ${results.length} tests · ${p2} passed · ${f2} failed${cNote}`)
        setRunState(msg.error ? 'error' : 'done')
      } else if (msg.type === 'error') {
        setSummary(`⚠ ${msg.message}`)
        setRunState('error')
      }
    }

    ws.onerror = () => { setSummary('WebSocket error — is the backend running?'); setRunState('error') }
    ws.onclose = () => { if (runState === 'running') setRunState('idle') }
  }

  const stateColor: Record<RunState, string> = {
    idle:    '#2d3058',
    running: '#ffb800',
    done:    '#00ff88',
    error:   '#ff2d55',
  }

  return (
    <div className="p-8 space-y-5">
      <h1 className="text-2xl font-bold font-mono tracking-widest text-[#e2e8f0]">
        <span className="text-cyan opacity-60 mr-2">&gt;</span>RUN TESTS
      </h1>

      {/* Controls */}
      <GlowCard title="TARGET">
        <div className="space-y-4">
          {/* Path input */}
          <div className="flex gap-3">
            <div className="relative flex-1">
              <FolderOpen size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#4a5568]" />
              <input
                value={path}
                onChange={e => setPath(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && runState === 'idle' && run()}
                placeholder="C:\path\to\your\project"
                className="cyber-input w-full pl-9"
                disabled={runState === 'running'}
              />
            </div>
            {runState === 'running' ? (
              <button onClick={stop} className="cyber-btn cyber-btn-red flex items-center gap-2">
                <Square size={12} />STOP
              </button>
            ) : (
              <button
                onClick={run}
                disabled={!path.trim()}
                className="cyber-btn cyber-btn-green flex items-center gap-2"
              >
                <Play size={12} />RUN
              </button>
            )}
            {runState === 'done' && (
              <button
                onClick={() => router.push('/results')}
                className="cyber-btn cyber-btn-primary flex items-center gap-2"
              >
                <Upload size={12} />VIEW RESULTS
              </button>
            )}
          </div>

          {/* Coverage + status */}
          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <div
                onClick={() => setCoverage(v => !v)}
                className={`w-9 h-5 rounded-full transition-colors relative ${coverage ? 'bg-[rgba(0,212,255,0.25)]' : 'bg-[#1e2035]'}`}
                style={{ border: `1px solid ${coverage ? 'rgba(0,212,255,0.5)' : '#2d3058'}` }}
              >
                <div className={`absolute top-[2px] w-3.5 h-3.5 rounded-full transition-all ${coverage ? 'left-[18px] bg-cyan' : 'left-[2px] bg-[#2d3058]'}`} />
              </div>
              <span className="text-xs font-mono text-[#4a5568] tracking-widest">COVERAGE</span>
              <span className="text-[10px] font-mono text-[#2d3058]">(requires pytest-cov)</span>
            </label>

            <div className="ml-auto flex items-center gap-2">
              <span className="status-dot" style={{ backgroundColor: stateColor[runState] }} />
              <span className="text-[10px] font-mono tracking-widest" style={{ color: stateColor[runState] }}>
                {runState.toUpperCase()}
              </span>
            </div>
          </div>

          {/* Summary */}
          {summary && (
            <div
              className="px-4 py-2.5 rounded border font-mono text-xs"
              style={{
                color:       runState === 'error' ? '#ff2d55' : '#00ff88',
                borderColor: runState === 'error' ? '#ff2d5530' : '#00ff8830',
                background:  runState === 'error' ? '#ff2d5508' : '#00ff8808',
              }}
            >
              {summary}
            </div>
          )}
        </div>
      </GlowCard>

      {/* Terminal */}
      <GlowCard title="OUTPUT">
        <div
          ref={termRef}
          className="terminal-wrap h-[420px]"
        >
          {output.length === 0 && runState === 'idle' && (
            <div className="text-[#1e2035] tracking-widest">
              $ waiting for input<span className="terminal-cursor" />
            </div>
          )}
          {output.map((line, i) => (
            <div key={i} style={{ color: lineColor(line), whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              {line || ' '}
            </div>
          ))}
          {runState === 'running' && (
            <span className="text-[#00ff88] animate-blink">█</span>
          )}
          {runState === 'done' && output.length > 0 && (
            <div className="flex items-center gap-2 mt-3 pt-3 border-t border-[#0d1a0d]">
              <CheckCircle2 size={13} className="text-[#00ff88]" />
              <span className="text-[#00ff88] text-xs font-mono tracking-widest">RUN COMPLETE</span>
            </div>
          )}
        </div>
      </GlowCard>
    </div>
  )
}
