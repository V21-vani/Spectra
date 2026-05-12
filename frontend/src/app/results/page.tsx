'use client'
import { useEffect, useState, useRef, useMemo, useCallback } from 'react'
import { Upload, FileJson, Download, Code, Trash2, Plus, ChevronUp, ChevronDown, ChevronsUpDown, Search } from 'lucide-react'
import { api } from '@/lib/api'
import { TestResult } from '@/lib/types'
import StatusBadge from '@/components/StatusBadge'
import GlowCard from '@/components/GlowCard'

function stem(p: string) {
  return p.replace(/\\/g, '/').split('/').pop()?.replace(/\.[^.]+$/, '') ?? p
}

const STATUSES = ['ALL', 'PASSED', 'FAILED', 'SKIPPED', 'ERROR']

type SortKey = 'test_file' | 'test_name' | 'status' | 'duration' | 'coverage'

export default function Results() {
  const [results,   setResults]   = useState<TestResult[]>([])
  const [search,    setSearch]    = useState('')
  const [stFilter,  setStFilter]  = useState('ALL')
  const [fileFilter,setFileFilter]= useState('ALL')
  const [sortKey,   setSortKey]   = useState<SortKey | null>(null)
  const [sortAsc,   setSortAsc]   = useState(true)
  const [showAdd,   setShowAdd]   = useState(false)
  const [addErr,    setAddErr]    = useState('')

  // Add-form fields
  const [aFile, setAFile] = useState('')
  const [aName, setAName] = useState('')
  const [aStat, setAStat] = useState('PASSED')
  const [aDur,  setADur]  = useState('0')
  const [aCov,  setACov]  = useState('0')

  const xmlRef  = useRef<HTMLInputElement>(null)
  const jsonRef = useRef<HTMLInputElement>(null)

  const load = useCallback(() => api.getResults().then(setResults).catch(console.error), [])
  useEffect(() => { load() }, [load])

  const uniqueFiles = useMemo(
    () => ['ALL', ...Array.from(new Set(results.map(r => stem(r.test_file)))).sort()],
    [results]
  )

  const displayed = useMemo(() => {
    let r = results
    if (stFilter !== 'ALL') r = r.filter(x => x.status === stFilter)
    if (fileFilter !== 'ALL') r = r.filter(x => stem(x.test_file) === fileFilter)
    if (search) {
      const q = search.toLowerCase()
      r = r.filter(x => x.test_name.toLowerCase().includes(q) || x.test_file.toLowerCase().includes(q))
    }
    if (sortKey) {
      r = [...r].sort((a, b) => {
        const av = a[sortKey], bv = b[sortKey]
        if (typeof av === 'number' && typeof bv === 'number')
          return sortAsc ? av - bv : bv - av
        return sortAsc
          ? String(av).localeCompare(String(bv))
          : String(bv).localeCompare(String(av))
      })
    }
    return r
  }, [results, stFilter, fileFilter, search, sortKey, sortAsc])

  function handleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(a => !a)
    else { setSortKey(key); setSortAsc(true) }
  }

  function SortIcon({ k }: { k: SortKey }) {
    if (sortKey !== k) return <ChevronsUpDown size={10} className="text-[#2d3058] ml-1 inline" />
    return sortAsc
      ? <ChevronUp size={10} className="text-cyan ml-1 inline" />
      : <ChevronDown size={10} className="text-cyan ml-1 inline" />
  }

  async function addTest() {
    setAddErr('')
    try {
      if (!aFile.trim()) throw new Error('Test file required')
      if (!aName.trim()) throw new Error('Test name required')
      const dur = parseFloat(aDur) || 0
      const cov = parseFloat(aCov) || 0
      if (cov < 0 || cov > 100) throw new Error('Coverage must be 0–100')
      await api.addResult({ test_file: aFile, test_name: aName, status: aStat as any, duration: dur, coverage: cov })
      setAFile(''); setAName(''); setADur('0'); setACov('0')
      load()
    } catch (e: any) { setAddErr(e.message) }
  }

  async function handleXml(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]; if (!f) return
    api.importXml(f).then(r => { setResults(r); e.target.value = '' }).catch(err => alert(err.message))
  }

  async function handleJson(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]; if (!f) return
    api.importJson(f).then(r => { setResults(r); e.target.value = '' }).catch(err => alert(err.message))
  }

  async function del(id: string) {
    await api.deleteResult(id)
    setResults(r => r.filter(x => x.id !== id))
  }

  async function clearAll() {
    if (!confirm('Clear all test results?')) return
    await api.clearResults()
    setResults([])
  }

  return (
    <div className="p-8 space-y-5">
      {/* Hidden file inputs */}
      <input ref={xmlRef}  type="file" accept=".xml"  className="hidden" onChange={handleXml} />
      <input ref={jsonRef} type="file" accept=".json" className="hidden" onChange={handleJson} />

      {/* Header + actions */}
      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-2xl font-bold font-mono tracking-widest text-[#e2e8f0] mr-auto">
          <span className="text-cyan opacity-60 mr-2">&gt;</span>RESULTS
        </h1>
        <button onClick={() => xmlRef.current?.click()}  className="cyber-btn cyber-btn-primary flex items-center gap-1.5"><Upload size={11} />XML</button>
        <button onClick={() => jsonRef.current?.click()} className="cyber-btn cyber-btn-ghost flex items-center gap-1.5"><FileJson size={11} />JSON</button>
        <a href={api.exportCsvUrl()}  target="_blank" rel="noopener" className="cyber-btn cyber-btn-ghost flex items-center gap-1.5"><Download size={11} />CSV</a>
        <a href={api.exportJsonUrl()} target="_blank" rel="noopener" className="cyber-btn cyber-btn-ghost flex items-center gap-1.5"><Code size={11} />JSON</a>
        <button onClick={clearAll} className="cyber-btn cyber-btn-red flex items-center gap-1.5"><Trash2 size={11} />CLEAR</button>
      </div>

      {/* Add manually */}
      <GlowCard>
        <button
          onClick={() => setShowAdd(v => !v)}
          className="flex items-center gap-2 text-xs font-mono text-[#4a5568] hover:text-[#e2e8f0] transition-colors w-full"
        >
          <Plus size={12} />
          <span className="tracking-widest">ADD TEST MANUALLY</span>
          <ChevronDown size={12} className={`ml-auto transition-transform ${showAdd ? 'rotate-180' : ''}`} />
        </button>
        {showAdd && (
          <div className="mt-4 space-y-3">
            <div className="flex gap-3 flex-wrap">
              <input value={aFile} onChange={e => setAFile(e.target.value)} placeholder="test_file / classname" className="cyber-input flex-1 min-w-[160px]" />
              <input value={aName} onChange={e => setAName(e.target.value)} placeholder="test_name"              className="cyber-input flex-1 min-w-[180px]" />
              <select value={aStat} onChange={e => setAStat(e.target.value)}
                className="cyber-input w-32"
                style={{ appearance: 'none' }}>
                {['PASSED','FAILED','SKIPPED','ERROR'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <input value={aDur} onChange={e => setADur(e.target.value)} placeholder="ms"  type="number" className="cyber-input w-24" />
              <input value={aCov} onChange={e => setACov(e.target.value)} placeholder="cov%" type="number" className="cyber-input w-24" />
              <button onClick={addTest} className="cyber-btn cyber-btn-primary flex items-center gap-1.5"><Plus size={11} />ADD</button>
            </div>
            {addErr && <p className="text-[#ff2d55] text-xs font-mono">{addErr}</p>}
          </div>
        )}
      </GlowCard>

      {/* Filter bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative">
          <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#4a5568]" />
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search tests…"
            className="cyber-input pl-8 w-56"
          />
        </div>
        <select value={stFilter} onChange={e => setStFilter(e.target.value)} className="cyber-input w-36" style={{ appearance: 'none' }}>
          {STATUSES.map(s => <option key={s} value={s}>{s === 'ALL' ? 'All Statuses' : s}</option>)}
        </select>
        <select value={fileFilter} onChange={e => setFileFilter(e.target.value)} className="cyber-input w-44" style={{ appearance: 'none' }}>
          {uniqueFiles.map(f => <option key={f} value={f}>{f === 'ALL' ? 'All Files' : f}</option>)}
        </select>
        <span className="ml-auto text-[10px] font-mono text-[#2d3058] tracking-widest">
          {displayed.length} RESULT{displayed.length !== 1 ? 'S' : ''}
        </span>
      </div>

      {/* Table */}
      <GlowCard>
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="border-b border-edge">
                {([
                  ['test_file', 'FILE'],
                  ['test_name', 'TEST'],
                  ['status',   'STATUS'],
                  ['duration', 'MS'],
                  ['coverage', 'COV %'],
                ] as [SortKey, string][]).map(([k, label]) => (
                  <th
                    key={k}
                    onClick={() => handleSort(k)}
                    className="py-2.5 px-4 text-left text-[#4a5568] font-normal tracking-widest cursor-pointer hover:text-[#e2e8f0] select-none transition-colors"
                  >
                    {label}<SortIcon k={k} />
                  </th>
                ))}
                <th className="py-2.5 px-4 text-left text-[#4a5568] font-normal tracking-widest">ERROR</th>
                <th className="py-2.5 px-4 w-10" />
              </tr>
            </thead>
            <tbody>
              {displayed.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-[#2d3058] tracking-widest">
                    NO RESULTS MATCH FILTERS
                  </td>
                </tr>
              ) : displayed.map(r => {
                const covColor = r.coverage > 0
                  ? r.coverage >= 80 ? '#00ff88' : r.coverage >= 50 ? '#ffb800' : '#ff2d55'
                  : '#2d3058'
                return (
                  <tr key={r.id} className="border-b border-edge hover:bg-surface2 transition-colors group">
                    <td className="py-2.5 px-4 text-[#e2e8f0] max-w-[150px] truncate" title={r.test_file}>{stem(r.test_file)}</td>
                    <td className="py-2.5 px-4 text-[#e2e8f0] max-w-[220px] truncate" title={r.test_name}>{r.test_name}</td>
                    <td className="py-2.5 px-4"><StatusBadge status={r.status} /></td>
                    <td className="py-2.5 px-4 text-[#4a5568] tabular-nums">{r.duration.toFixed(1)}</td>
                    <td className="py-2.5 px-4 tabular-nums font-bold" style={{ color: covColor }}>
                      {r.coverage > 0 ? `${r.coverage.toFixed(0)}%` : '—'}
                    </td>
                    <td className="py-2.5 px-4 text-[#ff2d55] max-w-[180px] truncate" title={r.error_message ?? ''}>
                      {r.error_message || <span className="text-[#2d3058]">—</span>}
                    </td>
                    <td className="py-2.5 px-2">
                      <button
                        onClick={() => del(r.id)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-[#ff2d55] hover:text-[#ff2d55] p-1 rounded hover:bg-[#ff2d5512]"
                      >
                        <Trash2 size={12} />
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </GlowCard>
    </div>
  )
}
