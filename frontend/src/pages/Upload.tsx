import { ChangeEvent, useEffect, useState } from 'react'
import api from '../api/client'

type SnapshotType = 'MORNING' | 'EOD'

interface MorningSnapshotInfo {
  id: number
  sprint: string
  report_date: string
  total_scope: number
  completed_sp: number
  completion_pct: number
}

interface DevRow {
  name: string
  assigned_sp: number
  completed_sp: number
  completion_pct: number
  morning_assigned: number | null
  morning_completed: number | null
  morning_pct: number | null
  movement_pct: number | null
}

interface UploadResult {
  report_id: number
  sprint: string
  report_date: string
  snapshot_type: string
  morning_source: string   // "none" | "uploaded" | "saved"
  total_scope: number
  completed_sp: number
  remaining_sp: number
  completion_pct: number
  total_stories: number
  completed_stories: number
  open_stories: number
  has_morning: boolean
  morning_scope: number | null
  morning_completed: number | null
  morning_pct: number | null
  daily_movement: number | null
  day1_fixed_scope: number | null
  developers: DevRow[]
  warnings: string[]
}

function fmt2(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  return n.toFixed(2)
}

function fmtPct(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  return `${n.toFixed(2)}%`
}

function fmtMov(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`
}

export default function Upload() {
  const [snapshotType, setSnapshotType] = useState<SnapshotType>('EOD')
  const [morningFile, setMorningFile] = useState<File | null>(null)
  const [eodFile, setEodFile]         = useState<File | null>(null)
  const [reportDate, setReportDate]   = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  })
  const [day1Scope, setDay1Scope]     = useState('')
  const [sprintStart, setSprintStart] = useState('')
  const [sprintEnd, setSprintEnd]     = useState('')
  const [loading, setLoading]         = useState(false)
  const [result, setResult]           = useState<UploadResult | null>(null)
  const [error, setError]             = useState<string | null>(null)
  const [deletingSnapshotId, setDeletingSnapshotId] = useState<number | null>(null)

  // Saved morning snapshots (for display hint)
  const [savedSnapshots, setSavedSnapshots] = useState<MorningSnapshotInfo[]>([])

  const loadSavedSnapshots = async () => {
    try {
      const r = await api.get('/reports/morning-snapshots')
      setSavedSnapshots(r.data)
    } catch {
      setSavedSnapshots([])
    }
  }

  useEffect(() => {
    loadSavedSnapshots()
  }, [result]) // refresh after each upload

  const pickFile = (e: ChangeEvent<HTMLInputElement>, setter: (f: File | null) => void) => {
    setter(e.target.files?.[0] ?? null)
    e.target.value = ''
  }

  const formatDateForApi = (iso: string) => {
    if (!iso) return ''
    const [y, m, d] = iso.split('-')
    return `${d}/${m}/${y}`
  }

  const formatDateTimeForApi = (localDateTime: string) => {
    if (!localDateTime) return ''
    const [datePart, timePart] = localDateTime.split('T')
    if (!datePart || !timePart) return ''
    const [y, m, d] = datePart.split('-')
    return `${d}/${m}/${y} ${timePart}`
  }

  const handleDeleteSavedSnapshot = async (snapshotId: number, sprint: string) => {
    const confirmed = window.confirm(`Delete saved morning snapshot for ${sprint}?`)
    if (!confirmed) return

    setDeletingSnapshotId(snapshotId)
    try {
      await api.delete(`/reports/morning-snapshots/${snapshotId}`)
      await loadSavedSnapshots()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unable to delete saved morning snapshot.')
    } finally {
      setDeletingSnapshotId(null)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const needsMorning = snapshotType === 'MORNING'
    const needsEod     = snapshotType === 'EOD'

    if (needsMorning && !morningFile) {
      setError('Please select a Morning CSV file.')
      return
    }
    if (needsEod && !eodFile) {
      setError('Please select an EOD CSV file.')
      return
    }

    const formData = new FormData()
    formData.append('snapshot_type', snapshotType)
    if (morningFile) formData.append('morning_file', morningFile)
    if (eodFile)     formData.append('eod_file',     eodFile)
    formData.append('report_date', formatDateForApi(reportDate))
    if (day1Scope)   formData.append('day1_fixed_scope', day1Scope)
    if (sprintStart) formData.append('sprint_start', formatDateTimeForApi(sprintStart))
    if (sprintEnd)   formData.append('sprint_end',   formatDateTimeForApi(sprintEnd))

    try {
      setLoading(true)
      setError(null)
      setResult(null)
      const res = await api.post('/reports/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Report generation failed.')
    } finally {
      setLoading(false)
    }
  }

  // Find if there's a saved morning snapshot that will auto-match today's date
  const todayFormatted = formatDateForApi(reportDate)
  const matchedSnapshot = savedSnapshots.find(s => s.report_date === todayFormatted)

  return (
    <div className="space-y-6 max-w-3xl">
      {/* ── Header ── */}
      <div>
        <p className="text-sm uppercase tracking-wide text-gray-500">Reports</p>
        <h1 className="text-3xl font-bold text-gray-900">Upload Jira CSV</h1>
      </div>

      {/* ── Upload form ── */}
      <form onSubmit={handleSubmit} className="card space-y-5">

        {/* Snapshot type selector */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">Snapshot Type</label>
          <div className="flex gap-3">
            {(['MORNING', 'EOD'] as SnapshotType[]).map(t => (
              <button
                key={t}
                type="button"
                onClick={() => { setSnapshotType(t); setError(null) }}
                className={`px-5 py-2 rounded-lg text-sm font-semibold border transition ${
                  snapshotType === t
                    ? 'bg-[#1F3864] text-white border-[#1F3864]'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-[#2E75B6]'
                }`}
              >
                {t === 'MORNING' ? '🌅 Morning Only' : '🌆 EOD'}
              </button>
            ))}
          </div>

          {/* Scenario explanation */}
          <div className="mt-2 text-xs text-gray-500 bg-gray-50 rounded-lg px-3 py-2">
            {snapshotType === 'MORNING' ? (
              <>
                <strong>Morning snapshot</strong> — saves morning data to DB.
                Upload EOD later today and the system will automatically match it.
              </>
            ) : (
              <>
                <strong>EOD report</strong> — optionally attach a Morning CSV too.
                If none is attached, the system will look for a saved Morning snapshot
                for <strong>{todayFormatted || 'the selected date'}</strong>.
                {matchedSnapshot && (
                  <span className="ml-1 text-green-700 font-medium">
                    ✓ Saved morning snapshot found ({matchedSnapshot.sprint}, {matchedSnapshot.completion_pct.toFixed(2)}% completion).
                  </span>
                )}
              </>
            )}
          </div>
        </div>

        {/* File inputs */}
        <div className="grid md:grid-cols-2 gap-5">
          {/* Morning file — shown for MORNING type or EOD type (optional) */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Morning CSV / TSV
              {snapshotType === 'MORNING'
                ? <span className="text-red-500 ml-1">*</span>
                : <span className="text-gray-400 font-normal ml-1">(optional)</span>
              }
            </label>
            <input
              type="file"
              accept=".csv,.tsv,.txt"
              onChange={e => pickFile(e, setMorningFile)}
              className="block w-full text-sm text-gray-600
                file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0
                file:bg-[#1F3864] file:text-white file:cursor-pointer
                hover:file:bg-[#2E75B6] transition"
            />
            {morningFile && <p className="mt-1 text-xs text-gray-500 truncate">{morningFile.name}</p>}
          </div>

          {/* EOD file — shown for EOD type */}
          {snapshotType === 'EOD' && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">
                EOD CSV / TSV <span className="text-red-500">*</span>
              </label>
              <input
                type="file"
                accept=".csv,.tsv,.txt"
                onChange={e => pickFile(e, setEodFile)}
                className="block w-full text-sm text-gray-600
                  file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0
                  file:bg-[#1F3864] file:text-white file:cursor-pointer
                  hover:file:bg-[#2E75B6] transition"
              />
              {eodFile && <p className="mt-1 text-xs text-gray-500 truncate">{eodFile.name}</p>}
            </div>
          )}
        </div>

        {/* Date + Sprint dates */}
        <div className="grid md:grid-cols-3 gap-5">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Report Date</label>
            <input
              type="date"
              value={reportDate}
              onChange={e => setReportDate(e.target.value)}
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Sprint Start <span className="font-normal text-gray-400">(optional)</span>
            </label>
            <input
              type="datetime-local"
              value={sprintStart}
              onChange={e => setSprintStart(e.target.value)}
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Sprint End <span className="font-normal text-gray-400">(optional)</span>
            </label>
            <input
              type="datetime-local"
              value={sprintEnd}
              onChange={e => setSprintEnd(e.target.value)}
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        {/* Day-1 Fixed Scope */}
        <div className="grid md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Day-1 Fixed Scope (SP) <span className="font-normal text-gray-400">(optional)</span>
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={day1Scope}
              onChange={e => setDay1Scope(e.target.value)}
              placeholder="e.g. 197.60"
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
            <p className="mt-1 text-xs text-gray-400">Used for Scope Change calculation. Leave blank to use saved value.</p>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <button type="submit" disabled={loading} className="btn-primary w-full md:w-auto">
          {loading ? 'Generating…' : snapshotType === 'MORNING' ? 'Save Morning Snapshot' : 'Generate Report'}
        </button>
      </form>

      {/* ── Result ── */}
      {result && <ResultCard result={result} />}

      {/* ── Saved morning snapshots ── */}
      {savedSnapshots.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Saved Morning Snapshots</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-100 text-left">
                <tr>
                  <th className="px-3 py-2 font-semibold">Sprint</th>
                  <th className="px-3 py-2 font-semibold">Date</th>
                  <th className="px-3 py-2 font-semibold">Scope (SP)</th>
                  <th className="px-3 py-2 font-semibold">Completed (SP)</th>
                  <th className="px-3 py-2 font-semibold">Completion %</th>
                </tr>
              </thead>
              <tbody>
                {savedSnapshots.map(s => (
                  <tr key={s.id} className="border-t border-gray-200">
                    <td className="px-3 py-2 font-medium">{s.sprint}</td>
                    <td className="px-3 py-2">{s.report_date}</td>
                    <td className="px-3 py-2">{s.total_scope.toFixed(2)}</td>
                    <td className="px-3 py-2">{s.completed_sp.toFixed(2)}</td>
                    <td className="px-3 py-2">{s.completion_pct.toFixed(2)}%</td>
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        onClick={() => handleDeleteSavedSnapshot(s.id, s.sprint)}
                        disabled={deletingSnapshotId === s.id}
                        className="text-red-600 hover:text-red-700 text-xs font-medium disabled:opacity-50"
                      >
                        {deletingSnapshotId === s.id ? 'Deleting…' : 'Delete'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Result card ───────────────────────────────────────────────────────────────

function ResultCard({ result }: { result: UploadResult }) {
  const isMorningOnly = result.snapshot_type === 'MORNING'

  return (
    <div className="card space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <p className="text-sm text-gray-500 uppercase tracking-wide">
            {isMorningOnly ? 'Morning Snapshot Saved' : 'Report Generated'}
          </p>
          <h2 className="text-2xl font-bold text-gray-900">{result.sprint}</h2>
          <p className="text-sm text-gray-500">{result.report_date}</p>
          {result.morning_source === 'saved' && (
            <p className="text-xs text-green-700 mt-0.5">
              ✓ Morning data automatically matched from saved snapshot
            </p>
          )}
          {result.morning_source === 'uploaded' && result.has_morning && (
            <p className="text-xs text-blue-700 mt-0.5">
              ✓ Morning + EOD both uploaded — Morning vs EOD comparison generated
            </p>
          )}
        </div>
        <a
          href={`/api/reports/${result.report_id}/download`}
          target="_blank"
          rel="noreferrer"
          className="btn-primary flex items-center gap-2 shrink-0"
        >
          ↓ Download Excel Report
        </a>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatTile label="Total Scope"   value={`${fmt2(result.total_scope)} SP`} />
        <StatTile label="Completed SP"  value={`${fmt2(result.completed_sp)} SP`} />
        <StatTile label="Remaining SP"  value={`${fmt2(result.remaining_sp)} SP`} />
        <StatTile label="Completion"    value={fmtPct(result.completion_pct)} />
      </div>

      {result.has_morning && !isMorningOnly && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatTile label="Morning Scope"     value={`${fmt2(result.morning_scope)} SP`} />
          <StatTile label="Morning Completed" value={`${fmt2(result.morning_completed)} SP`} />
          <StatTile label="Morning %"         value={fmtPct(result.morning_pct)} />
          <StatTile label="Daily Movement"    value={fmtMov(result.daily_movement)} />
        </div>
      )}

      {/* Developer table */}
      <div>
        <h3 className="font-semibold mb-2 text-gray-800">Developer breakdown</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm border border-gray-200">
            <thead className="bg-[#1F3864] text-white">
              <tr>
                <th className="px-3 py-2 text-left">Developer</th>
                {result.has_morning && (
                  <>
                    <th className="px-3 py-2 text-center">Morning SP</th>
                    <th className="px-3 py-2 text-center">Morning Done</th>
                    <th className="px-3 py-2 text-center">Morning %</th>
                  </>
                )}
                <th className="px-3 py-2 text-center">{isMorningOnly ? 'Assigned SP' : 'EOD SP'}</th>
                <th className="px-3 py-2 text-center">{isMorningOnly ? 'Completed SP' : 'EOD Done'}</th>
                <th className="px-3 py-2 text-center">{isMorningOnly ? 'Completion %' : 'EOD %'}</th>
                {result.has_morning && !isMorningOnly && (
                  <th className="px-3 py-2 text-center">Movement</th>
                )}
              </tr>
            </thead>
            <tbody>
              {result.developers.map((dev, i) => (
                <tr key={dev.name} className={i % 2 === 1 ? 'bg-[#DEEAF1]' : 'bg-white'}>
                  <td className="px-3 py-2 font-medium">{dev.name}</td>
                  {result.has_morning && (
                    <>
                      <td className="px-3 py-2 text-center">{fmt2(dev.morning_assigned)}</td>
                      <td className="px-3 py-2 text-center">{fmt2(dev.morning_completed)}</td>
                      <td className="px-3 py-2 text-center">{fmtPct(dev.morning_pct)}</td>
                    </>
                  )}
                  <td className="px-3 py-2 text-center">{dev.assigned_sp.toFixed(2)}</td>
                  <td className="px-3 py-2 text-center">{dev.completed_sp.toFixed(2)}</td>
                  <td className="px-3 py-2 text-center">{dev.completion_pct.toFixed(2)}%</td>
                  {result.has_morning && !isMorningOnly && (
                    <td className="px-3 py-2 text-center">{fmtMov(dev.movement_pct)}</td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <div>
          <h3 className="font-semibold mb-2 text-gray-800">
            Warnings <span className="font-normal text-gray-400">({result.warnings.length})</span>
          </h3>
          <ul className="space-y-1 text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-3 max-h-48 overflow-y-auto">
            {result.warnings.map((w, i) => (
              <li key={i} className="flex gap-2">
                <span className="shrink-0">•</span><span>{w}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-blue-50 border border-blue-100 p-3">
      <p className="text-xs text-gray-500 mb-0.5">{label}</p>
      <p className="text-lg font-bold text-gray-900 truncate">{value}</p>
    </div>
  )
}
