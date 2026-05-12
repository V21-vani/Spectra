import { Status } from '@/lib/types'

const THEME: Record<Status, { bg: string; text: string; border: string }> = {
  PASSED:  { bg: '#00ff8812', text: '#00ff88', border: '#00ff8830' },
  FAILED:  { bg: '#ff2d5512', text: '#ff2d55', border: '#ff2d5530' },
  SKIPPED: { bg: '#ffb80012', text: '#ffb800', border: '#ffb80030' },
  ERROR:   { bg: '#fb923c12', text: '#fb923c', border: '#fb923c30' },
}

export default function StatusBadge({ status }: { status: string }) {
  const t = THEME[status as Status] ?? { bg: '#ffffff10', text: '#888', border: '#88888830' }
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wider"
      style={{ backgroundColor: t.bg, color: t.text, border: `1px solid ${t.border}` }}
    >
      {status}
    </span>
  )
}
