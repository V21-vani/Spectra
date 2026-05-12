'use client'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { TestResult, STATUS_COLOR } from '@/lib/types'

export default function DurationBar({ results }: { results: TestResult[] }) {
  const top = [...results].sort((a, b) => b.duration - a.duration).slice(0, 10)
  const data = top.map(r => ({
    name: r.test_name.length > 22 ? r.test_name.slice(0, 22) + '…' : r.test_name,
    ms: parseFloat(r.duration.toFixed(1)),
    status: r.status,
  }))

  if (!data.length) {
    return (
      <div className="h-60 flex items-center justify-center text-[#2d3058] font-mono text-sm tracking-widest">
        NO DATA
      </div>
    )
  }

  const monoStyle = { fontFamily: 'monospace', fontSize: 10, fill: '#4a5568' }

  return (
    <div className="h-60">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 4, right: 24, top: 4, bottom: 4 }}>
          <XAxis type="number" tick={monoStyle} axisLine={false} tickLine={false} unit=" ms" />
          <YAxis type="category" dataKey="name" width={130}
            tick={{ fontFamily: 'monospace', fontSize: 10, fill: '#e2e8f0' }}
            axisLine={false} tickLine={false}
          />
          <Tooltip
            formatter={(v: number) => [`${v} ms`, 'Duration']}
            contentStyle={{ background: '#0a0b14', border: '1px solid #1e2035', borderRadius: 6, fontFamily: 'monospace', fontSize: 11 }}
            cursor={{ fill: 'rgba(255,255,255,0.03)' }}
          />
          <Bar dataKey="ms" radius={[0, 4, 4, 0]}>
            {data.map((e, i) => (
              <Cell key={i}
                fill={STATUS_COLOR[e.status as keyof typeof STATUS_COLOR] ?? '#888'}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
