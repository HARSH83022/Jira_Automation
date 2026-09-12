import { useEffect, useMemo, useState } from 'react'
import { BarChart, Bar, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, PieChart, Pie, Cell } from 'recharts'
import api from '../api/client'
import ProgressBar from '../components/ProgressBar'
import StatCard from '../components/StatCard'

const COLORS = ['#1F3864', '#2E75B6', '#7CB5EC', '#A7D6FF']

interface DevRow {
  name: string
  assigned_sp: number
  completed_sp: number
  remaining_sp: number
  completion_pct: number
}

interface ReportDetail {
  sprint?: string
  total_scope: number
  completed_sp: number
  remaining_sp?: number
  completion_percentage: number
  total_stories?: number
  completed_stories?: number
  open_stories?: number
  developer_data?: DevRow[]
  warnings?: string[] | null
}

export default function Dashboard() {
  const [report, setReport] = useState<ReportDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [sendType, setSendType] = useState<'MORNING' | 'EOD'>('EOD')
  const [sendStatus, setSendStatus] = useState('')
  const [sending, setSending] = useState(false)
  const [emailSchedule, setEmailSchedule] = useState<any>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [historyRes, emailRes] = await Promise.all([
          api.get('/reports/history'),
          api.get('/settings/email'),
        ])
        setEmailSchedule(emailRes.data)
        const latest = historyRes.data?.[0]
        if (latest) {
          const detail = await api.get(`/reports/${latest.id}`)
          setReport(detail.data)
        }
      } catch (error) {
        console.error('Unable to fetch report summary', error)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const developers: DevRow[] = report?.developer_data ?? []
  const completedSp   = report?.completed_sp ?? 0
  const totalScope    = report?.total_scope ?? 0
  const remainingSp   = Math.max(0, totalScope - completedSp)
  const completionPct = report?.completion_percentage ?? 0
  const warningCount  = Array.isArray(report?.warnings) ? report!.warnings!.length : 0

  const chartData = useMemo(
    () => developers.map((d) => ({ name: d.name, value: Number(d.completion_pct || 0) })),
    [developers]
  )

  const pieData = useMemo(
    () => [
      { name: 'Completed', value: completedSp },
      { name: 'Remaining', value: remainingSp },
    ],
    [completedSp, remainingSp]
  )

  const sendLatestReport = async () => {
    setSending(true)
    setSendStatus('Sending report email...')
    try {
      const response = await api.post(`/email/test?report_type=${sendType}`)
      setSendStatus(`Email sent successfully (${response.data.status}).`)
    } catch (error: any) {
      setSendStatus(error.response?.data?.detail || 'Email delivery failed.')
    } finally {
      setSending(false)
    }
  }

  if (loading) return <div className="card">Loading dashboard…</div>

  if (!report) {
    return (
      <div className="card">
        <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
        <p className="text-gray-600">No report generated yet. Upload a Jira CSV to get started.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-wide text-gray-500">Sprint overview</p>
        <h1 className="text-3xl font-bold text-gray-900">{report.sprint || 'Sprint Report'}</h1>
      </div>

      <div className="card flex flex-wrap items-center gap-3">
        <div>
          <p className="text-sm font-semibold text-gray-700">Send report email</p>
          <p className="text-xs text-gray-500">Use the latest generated snapshot for checking.</p>
        </div>
        <select
          value={sendType}
          onChange={(event) => setSendType(event.target.value as 'MORNING' | 'EOD')}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="MORNING">Morning</option>
          <option value="EOD">EOD</option>
        </select>
        <button onClick={sendLatestReport} disabled={sending} className="btn-primary disabled:opacity-50">
          {sending ? 'Sending…' : 'Send Mail'}
        </button>
        {sendStatus && <span className="text-sm text-gray-600">{sendStatus}</span>}
      </div>
      {emailSchedule && (
        <div className="text-sm text-gray-600">
          Automatic email schedule: Morning <strong>{emailSchedule.morning_time}</strong> · EOD <strong>{emailSchedule.eod_time}</strong> · {emailSchedule.timezone} ·{' '}
          {emailSchedule.enabled ? <span className="text-green-700 font-semibold">Enabled</span> : <span className="text-gray-500">Disabled</span>}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Scope"          value={`${totalScope.toFixed(2)} SP`}      sub="Current scope" />
        <StatCard label="Completed SP"         value={`${completedSp.toFixed(2)} SP`}     sub="Completed" />
        <StatCard label="Remaining SP"         value={`${remainingSp.toFixed(2)} SP`}     sub="Open" />
        <StatCard label="Overall Completion %" value={`${completionPct.toFixed(2)}%`}    sub="Delivery progress" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Stories"     value={report.total_stories     ?? '—'} />
        <StatCard label="Completed Stories" value={report.completed_stories ?? '—'} />
        <StatCard label="Open Stories"      value={report.open_stories      ?? '—'} />
        <StatCard label="Warnings"          value={warningCount} sub="Data quality checks" />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Developer completion %</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} interval={0} angle={-10} textAnchor="end" height={60} />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value: number) => [`${value.toFixed(2)}%`, 'Completion']} />
                <Bar dataKey="value" fill="#2E75B6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Completed vs Remaining SP</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90} paddingAngle={3}>
                  {pieData.map((entry, index) => (
                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => [`${Number(value).toFixed(2)} SP`, 'Story points']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {developers.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Developer table</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-gray-100 text-left">
                  <th className="px-3 py-3 font-semibold">Developer</th>
                  <th className="px-3 py-3 font-semibold">Assigned SP</th>
                  <th className="px-3 py-3 font-semibold">Completed SP</th>
                  <th className="px-3 py-3 font-semibold">Remaining SP</th>
                  <th className="px-3 py-3 font-semibold">Completion %</th>
                </tr>
              </thead>
              <tbody>
                {developers.map((dev) => (
                  <tr key={dev.name} className="border-t border-gray-200">
                    <td className="px-3 py-3 font-medium">{dev.name}</td>
                    <td className="px-3 py-3">{(dev.assigned_sp ?? 0).toFixed(2)}</td>
                    <td className="px-3 py-3">{(dev.completed_sp ?? 0).toFixed(2)}</td>
                    <td className="px-3 py-3">{(dev.remaining_sp ?? 0).toFixed(2)}</td>
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-32">
                          <ProgressBar value={dev.completion_pct ?? 0} max={100} color="bg-brand-mid" />
                        </div>
                        <span>{(dev.completion_pct ?? 0).toFixed(2)}%</span>
                      </div>
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
