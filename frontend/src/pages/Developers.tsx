import { useEffect, useState } from 'react'
import api from '../api/client'
import type { Developer } from '../types'

export default function DevelopersPage() {
  const [developers, setDevelopers] = useState<Developer[]>([])
  const [name, setName] = useState('')

  const load = async () => {
    const response = await api.get('/developers/')
    setDevelopers(response.data)
  }

  useEffect(() => {
    load()
  }, [])

  const addDeveloper = async () => {
    if (!name.trim()) return
    await api.post('/developers/', { name, is_active: true })
    setName('')
    load()
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-wide text-gray-500">Configuration</p>
        <h1 className="text-3xl font-bold text-gray-900">Development team</h1>
      </div>

      <div className="card max-w-xl space-y-4">
        <div className="flex gap-3">
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Add developer name" className="flex-1 rounded-lg border border-gray-300 px-3 py-2" />
          <button onClick={addDeveloper} className="btn-primary">Add</button>
        </div>
      </div>

      <div className="card">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="px-3 py-3 font-semibold">Name</th>
              <th className="px-3 py-3 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody>
            {developers.map((developer) => (
              <tr key={developer.id} className="border-t border-gray-200">
                <td className="px-3 py-3">{developer.name}</td>
                <td className="px-3 py-3">{developer.is_active ? 'Active' : 'Inactive'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
