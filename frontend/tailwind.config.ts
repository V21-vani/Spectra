import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        bg:       '#030305',
        surface:  '#0a0b14',
        surface2: '#10112a',
        edge:     '#1e2035',
        'edge-hi':'#2d3058',
        cyan:  { DEFAULT: '#00d4ff', dim: '#0099bb' },
        neon:  {
          green:  '#00ff88',
          red:    '#ff2d55',
          yellow: '#ffb800',
          orange: '#fb923c',
          purple: '#8b5cf6',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glow-cyan':  '0 0 24px rgba(0,212,255,0.35)',
        'glow-green': '0 0 24px rgba(0,255,136,0.35)',
        'glow-red':   '0 0 24px rgba(255,45,85,0.35)',
        card:         '0 4px 30px rgba(0,0,0,0.6)',
      },
      keyframes: {
        blink: {
          '0%,100%': { opacity: '1' },
          '50%':     { opacity: '0' },
        },
        'glow-pulse': {
          '0%,100%': { boxShadow: '0 0 10px rgba(0,212,255,0.2)' },
          '50%':     { boxShadow: '0 0 30px rgba(0,212,255,0.5)' },
        },
        scan: {
          '0%':   { transform: 'translateY(-5%)' },
          '100%': { transform: 'translateY(105vh)' },
        },
      },
      animation: {
        blink:       'blink 1s step-end infinite',
        'glow-pulse':'glow-pulse 3s ease-in-out infinite',
        scan:        'scan 7s linear infinite',
      },
    },
  },
  plugins: [],
}

export default config
