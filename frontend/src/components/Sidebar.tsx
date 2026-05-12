'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, Table2, Play, History, Zap } from 'lucide-react'

const NAV = [
  { href: '/',         icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/results',  icon: Table2,          label: 'Results'   },
  { href: '/run',      icon: Play,            label: 'Run Tests' },
  { href: '/history',  icon: History,         label: 'History'   },
]

export default function Sidebar() {
  const path = usePathname()

  return (
    <aside className="w-56 h-screen flex flex-col shrink-0 border-r border-edge bg-surface">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-edge">
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded flex items-center justify-center"
            style={{ background: 'rgba(0,212,255,0.08)', border: '1px solid rgba(0,212,255,0.25)' }}
          >
            <Zap size={15} className="text-cyan" strokeWidth={2} />
          </div>
          <div>
            <div className="text-cyan font-mono font-bold text-sm tracking-[0.2em]">SPECTRA</div>
            <div className="text-[#4a5568] text-[10px] font-mono">v2.0 // analytics</div>
          </div>
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex-1 p-3 space-y-0.5">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = path === href
          return (
            <Link
              key={href}
              href={href}
              className={[
                'flex items-center gap-3 px-3 py-2.5 rounded text-xs font-mono transition-all',
                active
                  ? 'text-cyan bg-[rgba(0,212,255,0.08)] border-l-2 border-cyan pl-[10px]'
                  : 'text-[#4a5568] hover:text-[#e2e8f0] hover:bg-surface2 border-l-2 border-transparent pl-[10px]',
              ].join(' ')}
            >
              <Icon
                size={14}
                strokeWidth={active ? 2.2 : 1.8}
                style={{ color: active ? '#00d4ff' : undefined }}
              />
              <span className="tracking-wider">{label.toUpperCase()}</span>
            </Link>
          )
        })}
      </nav>

      {/* System status */}
      <div className="px-4 py-4 border-t border-edge space-y-1.5">
        <div className="flex items-center gap-2">
          <span className="status-dot bg-[#00ff88]" />
          <span className="text-[#00ff88] text-[10px] font-mono tracking-widest">SYSTEM ONLINE</span>
        </div>
        <div className="text-[#2d3058] text-[10px] font-mono">api :8000 · ui :3000</div>
      </div>
    </aside>
  )
}
