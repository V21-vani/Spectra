import { ReactNode } from 'react'

interface Props {
  title?: string
  children: ReactNode
  className?: string
  accent?: string   // hex colour for the top border accent
}

export default function GlowCard({ title, children, className = '', accent }: Props) {
  return (
    <div
      className={`bg-surface border border-edge rounded-lg overflow-hidden ${className}`}
      style={{ boxShadow: '0 4px 30px rgba(0,0,0,0.55), 0 0 1px rgba(0,212,255,0.08)' }}
    >
      {/* coloured top accent line */}
      <div
        className="h-[2px] w-full"
        style={{ background: accent ? `linear-gradient(90deg, ${accent}88, transparent)` : 'linear-gradient(90deg, rgba(0,212,255,0.5), transparent)' }}
      />
      {title && (
        <div className="px-5 py-3 border-b border-edge flex items-center gap-2">
          <span className="text-cyan text-xs font-mono opacity-70">//</span>
          <span className="text-[#e2e8f0] text-xs font-mono font-semibold tracking-widest">
            {title}
          </span>
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  )
}
