import { LucideIcon } from 'lucide-react'

interface Props {
  label: string
  value: string | number
  color: string
  icon: LucideIcon
}

export default function StatCard({ label, value, color, icon: Icon }: Props) {
  return (
    <div
      className="bg-surface border rounded-lg p-4 flex flex-col items-center gap-2 transition-all hover:scale-[1.02]"
      style={{
        borderColor: color + '33',
        boxShadow: `0 4px 20px rgba(0,0,0,0.45), 0 0 18px ${color}0e`,
      }}
    >
      <Icon size={17} style={{ color }} strokeWidth={1.8} />
      <div
        className="text-3xl font-bold font-mono leading-none"
        style={{ color, textShadow: `0 0 20px ${color}55` }}
      >
        {value}
      </div>
      <div className="text-[10px] font-mono tracking-[0.15em] text-[#4a5568]">{label}</div>
    </div>
  )
}
