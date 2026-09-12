import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../api/client'
import type { ReportDetailResponse } from '../types'

export default function ReportDetail() {
  const { id } = useParams()
  const [report, setReport] = useState<ReportDetailResponse | null>(null)

  useEffect(() => {
    const load = async () => {
      if (!id) return
      const response = await api.get(`/reports/${id}`)
      setReport(response.data)
    }
    load()
  }, [id])

  if (!report) return <div className="card">Loading report…</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide text-gray-500">Report</p>
          <h1 className="text-3xl font-bold text-gray-900">{report.sprint}</h1>
        </div>
        <div className="flex gap-2">
          <a href={`/api/reports/${id}/preview`} className="btn-secondary" target="_blank" rel="noreferrer">Preview Excel</a>
          <a href={`/api/reports/${id}/download`} className="btn-primary" target="_blank" rel="noreferrer">Download Excel</a>
        </div>
      </div>

      <div className="grid md:grid-cols-4 gap-4">
        <div className="card"><p className="text-sm text-gray-500">Total scope</p><p className="text-2xl font-bold">{report.total_scope.toFixed(2)} SP</p></div>
        <div className="card"><p className="text-sm text-gray-500">Completed</p><p className="text-2xl font-bold">{report.completed_sp.toFixed(2)} SP</p></div>
        <div className="card"><p className="text-sm text-gray-500">Remaining</p><p className="text-2xl font-bold">{report.remaining_sp.toFixed(2)} SP</p></div>
        <div className="card"><p className="text-sm text-gray-500">Completion</p><p className="text-2xl font-bold">{report.completion_pct.toFixed(2)}%</p></div>
      </div>

      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Developer summary</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-100 text-left">
              <tr>
                <th className="px-3 py-3 font-semibold">Developer</th>
                <th className="px-3 py-3 font-semibold">Assigned</th>
                <th className="px-3 py-3 font-semibold">Completed</th>
                <th className="px-3 py-3 font-semibold">Remaining</th>
                <th className="px-3 py-3 font-semibold">Completion</th>
              </tr>
            </thead>
            <tbody>
              {report.developers.map((developer) => (
                <tr key={developer.name} className="border-t border-gray-200">
                  <td className="px-3 py-3 font-medium">{developer.name}</td>
                  <td className="px-3 py-3">{developer.assigned_sp.toFixed(2)}</td>
                  <td className="px-3 py-3">{developer.completed_sp.toFixed(2)}</td>
                  <td className="px-3 py-3">{developer.remaining_sp.toFixed(2)}</td>
                  <td className="px-3 py-3">{developer.completion_pct.toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {report.warnings?.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold mb-3">Data quality warnings</h2>
          <ul className="list-disc ml-5 space-y-1 text-sm text-gray-700">
            {report.warnings.map((warning, index) => <li key={`${warning}-${index}`}>{warning}</li>)}
          </ul>
        </div>
      )}

      <Link to="/history" className="text-brand-mid hover:underline">← Back to reports</Link>
    </div>
  )
}
