'use client'
import { useEffect, useState, useCallback } from 'react'
import { CheckCircle, XCircle, SkipForward, AlertTriangle, TrendingUp, Timer, RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'
import { TestResult } from '@/lib/types'
import StatCard from '@/components/StatCard'
import GlowCard from '@/components/GlowCard'
import StatusPie from '@/components/charts/StatusPie'
import DurationBar from '@/components/charts/DurationBar'
import TrendBar from '@/components/charts/TrendBar'
import CoverageBar from '@/components/charts/CoverageBar'

function stem(p: string) {
  return p.replace(/\\/g, '/').split('/').pop()?.replace(/\.[^.]+$/, '') ?? p
}

export default function Dashboard() {
  const [results, setResults] = useState<TestResult[]>([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')

  const refresh = useCallback(() => {
    setErr('')
    api.getResults()
      .then(setResults)
      .catch(() => setErr('Cannot reach API — is the backend running on :8000?'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const total    = results.length
  const passed   = results.filter(r => r.status === 'PASSED').length
  const failed   = results.filter(r => r.status === 'FAILED').length
  const skipped  = results.filter(r => r.status === 'SKIPPED').length
  const errors   = results.filter(r => r.status === 'ERROR').length
  const passRate = total ? (passed / total * 100) : 0
  const totalMs  = results.reduce((s, r) => s + r.duration, 0)
  const hasCov   = results.some(r => r.coverage > 0)
  const avgCov   = hasCov ? results.reduce((s, r) => s + r.coverage, 0) / total : 0

  const runtimeStr = totalMs >= 60000
    ? `${(totalMs / 60000).toFixed(1)}m`
    : totalMs >= 1000
    ? `${(totalMs / 1000).toFixed(2)}s`
    : `${Math.round(totalMs)}ms`

  // Per-file breakdown
  const fileMap = new Map<string, { total: number; passed: number; failed: number }>()
  for (const r of results) {
    const key = stem(r.test_file)
    if (!fileMap.has(key)) fileMap.set(key, { total: 0, passed: 0, failed: 0 })
    const s = fileMap.get(key)!
    s.total++
    if (r.status === 'PASSED') s.passed++
    else if (r.status === 'FAILED' || r.status === 'ERROR') s.failed++
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold font-mono tracking-widest text-[#e2e8f0]">
            <span className="text-cyan opacity-60 mr-2">&gt;</span>DASHBOARD
          </h1>
          <p className="text-[#2d3058] text-xs font-mono mt-1">
            {loading ? 'LOADING…' : err ? 'ERROR' : `${total} tests · refreshed ${new Date().toLocaleTimeString()}`}
          </p>
        </div>
        <button onClick={refresh} className="cyber-btn cyber-btn-primary flex items-center gap-2">
          <RefreshCw size={12} />
          REFRESH
        </button>
      </div>

      {err && (
        <div className="border border-[#ff2d5540] bg-[#ff2d5508] rounded-lg px-5 py-3 text-[#ff2d55] font-mono text-xs">
          ⚠ {err}
        </div>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-6 gap-3">
        <StatCard label="PASSED"    value={passed}                color="#00ff88" icon={CheckCircle} />
        <StatCard label="FAILED"    value={failed}                color="#ff2d55" icon={XCircle} />
        <StatCard label="SKIPPED"   value={skipped}               color="#ffb800" icon={SkipForward} />
        <StatCard label="ERRORS"    value={errors}                color="#fb923c" icon={AlertTriangle} />
        <StatCard label="PASS RATE" value={`${passRate.toFixed(1)}%`} color="#00d4ff" icon={TrendingUp} />
        <StatCard label="RUNTIME"   value={runtimeStr}             color="#8b5cf6" icon={Timer} />
      </div>

      {/* Sub-stats */}
      <div className="flex gap-6 text-[10px] font-mono text-[#2d3058] tracking-widest">
        <span>TOTAL <span className="text-[#4a5568]">{total}</span></span>
        <span>·</span>
        <span>AVG DURATION <span className="text-[#4a5568]">{total ? (totalMs / total).toFixed(1) : 0} ms</span></span>
        <span>·</span>
        <span>
          AVG COVERAGE{' '}
          <span className={hasCov ? 'text-[#4a5568]' : 'text-[#1e2035]'}>
            {hasCov ? `${avgCov.toFixed(1)}%` : 'not collected'}
          </span>
        </span>
      </div>

      {/* Chart row 1 */}
      <div className="grid grid-cols-2 gap-5">
        <GlowCard title="STATUS DISTRIBUTION">
          <StatusPie results={results} />
        </GlowCard>
        <GlowCard title="SLOWEST TESTS">
          <DurationBar results={results} />
        </GlowCard>
      </div>

      {/* Chart row 2 — only when data exists */}
      {total > 0 && (
        <div className={`grid gap-5 ${hasCov ? 'grid-cols-2' : 'grid-cols-1'}`}>
          <GlowCard title="PASS / FAIL BY FILE">
            <TrendBar results={results} />
          </GlowCard>
          {hasCov && (
            <GlowCard title="COVERAGE BY FILE" accent="#00ff88">
              <CoverageBar results={results} />
            </GlowCard>
          )}
        </div>
      )}

      {/* Per-file table */}
      <GlowCard title="PER-FILE BREAKDOWN">
        {fileMap.size === 0 ? (
          <div className="py-10 text-center text-[#2d3058] font-mono text-xs tracking-widest">
            NO DATA LOADED — IMPORT XML OR RUN PYTEST
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono">
              <thead>
                <tr className="border-b border-edge">
                  {['FILE', 'TOTAL', 'FAILED', 'PASS RATE'].map(h => (
                    <th key={h} className={`py-2 px-4 text-[#4a5568] font-normal tracking-widest ${h !== 'FILE' ? 'text-right' : 'text-left'}`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Array.from(fileMap.entries()).slice(0, 12).map(([fname, s]) => {
                  const rate  = s.total ? s.passed / s.total * 100 : 0
                  const rCol  = rate === 100 ? '#00ff88' : rate < 50 ? '#ff2d55' : '#ffb800'
                  return (
                    <tr key={fname} className="border-b border-edge hover:bg-surface2 transition-colors">
                      <td className="py-2.5 px-4 text-[#e2e8f0]">{fname}</td>
                      <td className="py-2.5 px-4 text-right text-[#4a5568]">{s.total}</td>
                      <td className="py-2.5 px-4 text-right" style={{ color: s.failed ? '#ff2d55' : '#2d3058' }}>{s.failed}</td>
                      <td className="py-2.5 px-4 text-right font-bold" style={{ color: rCol }}>{rate.toFixed(0)}%</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </GlowCard>
    </div>
  )
}
