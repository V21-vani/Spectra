'use client'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts'
import { TestResult } from '@/lib/types'

function stem(p: string) {
  const parts = p.replace(/\\/g, '/').split('/')
  return (parts.pop() ?? p).replace(/\.[^.]+$/, '')
}

export default function CoverageBar({ results }: { results: TestResult[] }) {
  const map: Record<string, number[]> = {}
  for (const r of results) {
    if (r.coverage > 0) {
      const k = stem(r.test_file)
      if (!map[k]) map[k] = []
      map[k].push(r.coverage)
    }
  }

  const data = Object.entries(map).slice(0, 10).map(([name, covs]) => ({
    name,
    cov: parseFloat((covs.reduce((a, b) => a + b, 0) / covs.length).toFixed(1)),
  }))

  if (!data.length) {
    return (
      <div className="h-60 flex items-center justify-center text-[#2d3058] font-mono text-sm tracking-widest">
        NO COVERAGE DATA
      </div>
    )
  }

  const monoStyle = { fontFamily: 'monospace', fontSize: 10 }

  return (
    <div className="h-60">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 4, right: 24, top: 4, bottom: 4 }}>
          <XAxis type="number" domain={[0, 100]} tick={{ ...monoStyle, fill: '#4a5568' }}
            axisLine={false} tickLine={false} unit="%" />
          <YAxis type="category" dataKey="name" width={100}
            tick={{ ...monoStyle, fill: '#e2e8f0' }} axisLine={false} tickLine={false} />
          <ReferenceLine x={80} stroke="rgba(0,212,255,0.3)" strokeDasharray="4 3" />
          <Tooltip
            formatter={(v: number) => [`${v}%`, 'Avg Coverage']}
            contentStyle={{ background: '#0a0b14', border: '1px solid #1e2035', borderRadius: 6, fontFamily: 'monospace', fontSize: 11 }}
            cursor={{ fill: 'rgba(255,255,255,0.03)' }}
          />
          <Bar dataKey="cov" radius={[0, 4, 4, 0]}>
            {data.map((e, i) => (
              <Cell key={i}
                fill={e.cov >= 80 ? '#00ff88' : e.cov >= 50 ? '#ffb800' : '#ff2d55'}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
