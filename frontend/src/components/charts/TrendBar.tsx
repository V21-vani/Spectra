'use client'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TestResult } from '@/lib/types'

function stem(p: string) {
  const parts = p.replace(/\\/g, '/').split('/')
  return (parts.pop() ?? p).replace(/\.[^.]+$/, '')
}

export default function TrendBar({ results }: { results: TestResult[] }) {
  const map: Record<string, { passed: number; failed: number; skipped: number }> = {}
  for (const r of results) {
    const k = stem(r.test_file)
    if (!map[k]) map[k] = { passed: 0, failed: 0, skipped: 0 }
    if (r.status === 'PASSED') map[k].passed++
    else if (r.status === 'FAILED' || r.status === 'ERROR') map[k].failed++
    else map[k].skipped++
  }

  const data = Object.entries(map).slice(0, 10).map(([name, v]) => ({ name, ...v }))

  if (!data.length) {
    return (
      <div className="h-60 flex items-center justify-center text-[#2d3058] font-mono text-sm tracking-widest">
        NO DATA
      </div>
    )
  }

  const tickStyle = { fontFamily: 'monospace', fontSize: 10 }

  return (
    <div className="h-60">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: 4, right: 8, top: 4, bottom: 28 }}>
          <XAxis dataKey="name"
            tick={{ ...tickStyle, fill: '#e2e8f0' }}
            axisLine={false} tickLine={false}
            interval={0} angle={-30} textAnchor="end" height={50}
          />
          <YAxis tick={{ ...tickStyle, fill: '#4a5568' }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ background: '#0a0b14', border: '1px solid #1e2035', borderRadius: 6, fontFamily: 'monospace', fontSize: 11 }}
            cursor={{ fill: 'rgba(255,255,255,0.03)' }}
          />
          <Legend
            iconSize={7} iconType="circle"
            formatter={v => <span style={{ color: '#e2e8f0', fontFamily: 'monospace', fontSize: 10 }}>{v}</span>}
          />
          <Bar dataKey="passed"  fill="#00ff88" fillOpacity={0.85} radius={[3,3,0,0]} />
          <Bar dataKey="failed"  fill="#ff2d55" fillOpacity={0.85} radius={[3,3,0,0]} />
          <Bar dataKey="skipped" fill="#ffb800" fillOpacity={0.85} radius={[3,3,0,0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
