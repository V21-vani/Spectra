import type { Metadata } from 'next'
import './globals.css'
import Sidebar from '@/components/Sidebar'

export const metadata: Metadata = {
  title: 'Spectra // Test Analytics',
  description: 'Cybersec-grade test analytics platform',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        {/* Moving scan line */}
        <div
          className="pointer-events-none fixed left-0 right-0 h-[3px] z-[9998] animate-scan"
          style={{ background: 'linear-gradient(to bottom, transparent, rgba(0,212,255,0.04), transparent)', top: 0 }}
        />
        <div className="flex h-screen overflow-hidden cyber-grid">
          <Sidebar />
          <main className="flex-1 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  )
}
