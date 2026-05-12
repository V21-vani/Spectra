'use client'
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TestResult, STATUS_COLOR } from '@/lib/types'

export default function StatusPie({ results }: { results: TestResult[] }) {
  const counts: Record<string, number> = {}
  for (const r of results) counts[r.status] = (counts[r.status] ?? 0) + 1

  const data = Object.entries(counts)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value }))

  if (!data.length) {
    return (
      <div className="h-60 flex items-center justify-center text-[#2d3058] font-mono text-sm tracking-widest">
        NO DATA
      </div>
    )
  }

  return (
    <div className="h-60">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} cx="50%" cy="50%"
            innerRadius="55%" outerRadius="78%"
            paddingAngle={3} dataKey="value"
          >
            {data.map((e, i) => (
              <Cell key={i}
                fill={STATUS_COLOR[e.name as keyof typeof STATUS_COLOR] ?? '#888'}
                strokeWidth={0}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: '#0a0b14', border: '1px solid #1e2035', borderRadius: 6, fontFamily: 'monospace', fontSize: 11 }}
            itemStyle={{ color: '#e2e8f0' }}
          />
          <Legend
            iconType="circle" iconSize={7}
            formatter={v => <span style={{ color: '#e2e8f0', fontFamily: 'monospace', fontSize: 10, letterSpacing: '0.1em' }}>{v}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
