import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Download, Eye, Trash2 } from 'lucide-react'
import api from '../api/client'
import type { ReportHistory } from '../types'

export default function History() {
  const [items, setItems] = useState<ReportHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<number | null>(null)

  const load = async () => {
    try {
      const response = await api.get('/reports/history')
      setItems(response.data)
    } catch (error) {
      console.error('History fetch failed', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleDelete = async (id: number, sprint: string) => {
    if (!confirm(`Delete report for ${sprint}? This cannot be undone.`)) return
    setDeleting(id)
    try {
      await api.delete(`/reports/${id}`)
      setItems(prev => prev.filter(r => r.id !== id))
    } catch (err) {
      console.error('Delete failed', err)
    } finally {
      setDeleting(null)
    }
  }

  if (loading) return <div className="card">Loading report history…</div>

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-wide text-gray-500">History</p>
        <h1 className="text-3xl font-bold text-gray-900">Reports</h1>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-100 text-left">
              <tr>
                <th className="px-3 py-3 font-semibold">Sprint</th>
                <th className="px-3 py-3 font-semibold">Date</th>
                <th className="px-3 py-3 font-semibold">Type</th>
                <th className="px-3 py-3 font-semibold">Scope</th>
                <th className="px-3 py-3 font-semibold">Completed</th>
                <th className="px-3 py-3 font-semibold">Completion</th>
                <th className="px-3 py-3 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t border-gray-200 hover:bg-gray-50">
                  <td className="px-3 py-3 font-medium">{item.sprint || 'N/A'}</td>
                  <td className="px-3 py-3">{item.report_date || item.created_at || 'N/A'}</td>
                  <td className="px-3 py-3">
                    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                      item.snapshot_type === 'MORNING' 
                        ? 'bg-amber-100 text-amber-800' 
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {item.snapshot_type}
                    </span>
                  </td>
                  <td className="px-3 py-3">{item.total_scope.toFixed(2)}</td>
                  <td className="px-3 py-3">{item.completed_sp.toFixed(2)}</td>
                  <td className="px-3 py-3">{item.completion_percentage.toFixed(2)}%</td>
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-2">
                      <Link
                        to={`/reports/${item.id}`}
                        className="text-brand-mid font-medium hover:underline text-xs"
                      >
                        View
                      </Link>
                      <a
                        href={`/api/reports/${item.id}/preview`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-brand-mid hover:text-blue-700"
                        title="Preview Excel in browser"
                      >
                        <Eye className="w-4 h-4" />
                      </a>
                      <a
                        href={`/api/reports/${item.id}/download`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-green-600 hover:text-green-700"
                        title="Download Excel"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                      <button
                        onClick={() => handleDelete(item.id, item.sprint || 'report')}
                        disabled={deleting === item.id}
                        className="text-red-600 hover:text-red-700 disabled:opacity-50"
                        title="Delete report"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {items.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-gray-500">No reports generated yet. Upload a CSV to get started.</p>
        </div>
      )}
    </div>
  )
}
