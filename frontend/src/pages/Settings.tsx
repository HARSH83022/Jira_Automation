import { useEffect, useState } from 'react'
import api from '../api/client'

export default function SettingsPage() {
  const [statuses, setStatuses] = useState<string[]>([]) 
  const [draft, setDraft] = useState('')
  const [email, setEmail] = useState<any>({
    sender_email: '', recipients: [], cc: [], subject: '',
    report_type: 'EOD', morning_time: '09:30', eod_time: '18:30',
    timezone: 'Asia/Kolkata', days: [0, 1, 2, 3, 4], enabled: false,
    jira_csv_path: '',
  })
  const [emailMessage, setEmailMessage] = useState('')

  const load = async () => {
    const [statusResponse, emailResponse] = await Promise.all([
      api.get('/settings/statuses'),
      api.get('/settings/email'),
    ])
    setStatuses(statusResponse.data.statuses || [])
    setEmail(emailResponse.data)
  }

  useEffect(() => {
    load()
  }, [])

  const save = async () => {
    if (!statuses.length) return
    await api.put('/settings/statuses', { statuses })
  }

  const saveEmail = async () => {
    const response = await api.put('/settings/email', email)
    setEmail(response.data)
    setEmailMessage('Email automation settings saved.')
  }

  const sendTestEmail = async () => {
    setEmailMessage('Sending test email...')
    try {
      const response = await api.post('/email/test')
      setEmailMessage(`Test email ${response.data.status.toLowerCase()}.`)
    } catch (error: any) {
      setEmailMessage(error.response?.data?.detail || 'Test email failed.')
    }
  }

  const addStatus = () => {
    if (!draft.trim()) return
    setStatuses((current) => [...current, draft.trim()])
    setDraft('')
  }

  const removeStatus = (value: string) => {
    setStatuses((current) => current.filter((status) => status !== value))
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-wide text-gray-500">Configuration</p>
        <h1 className="text-3xl font-bold text-gray-900">Status settings</h1>
      </div>

      <div className="card max-w-xl space-y-4">
        <div className="flex gap-3">
          <input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Add status" className="flex-1 rounded-lg border border-gray-300 px-3 py-2" />
          <button onClick={addStatus} className="btn-primary">Add</button>
        </div>

        <div className="flex flex-wrap gap-2">
          {statuses.map((status) => (
            <button key={status} type="button" onClick={() => removeStatus(status)} className="rounded-full bg-gray-100 px-3 py-1 text-sm hover:bg-red-50 hover:text-red-700">
              {status} ×
            </button>
          ))}
        </div>

        <button onClick={save} className="btn-secondary">Save statuses</button>
      </div>

      <div className="card max-w-3xl space-y-4">
        <div>
          <p className="text-sm uppercase tracking-wide text-gray-500">Email Automation</p>
          <h2 className="text-xl font-bold text-gray-900">Gmail delivery</h2>
          <p className="text-xs text-gray-500 mt-1">Credentials remain server-side in backend/.env.</p>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <input className="rounded-lg border border-gray-300 px-3 py-2" placeholder="Sender email" value={email.sender_email || ''} onChange={e => setEmail({...email, sender_email: e.target.value})} />
          <input className="rounded-lg border border-gray-300 px-3 py-2" placeholder="Recipients (comma separated)" value={(email.recipients || []).join(', ')} onChange={e => setEmail({...email, recipients: e.target.value.split(',').map((v: string) => v.trim()).filter(Boolean)})} />
          <input className="rounded-lg border border-gray-300 px-3 py-2" placeholder="CC (comma separated)" value={(email.cc || []).join(', ')} onChange={e => setEmail({...email, cc: e.target.value.split(',').map((v: string) => v.trim()).filter(Boolean)})} />
          <input className="rounded-lg border border-gray-300 px-3 py-2" placeholder="Subject (optional)" value={email.subject || ''} onChange={e => setEmail({...email, subject: e.target.value})} />
          <select className="rounded-lg border border-gray-300 px-3 py-2" value={email.report_type} onChange={e => setEmail({...email, report_type: e.target.value})}><option value="MORNING">Morning</option><option value="EOD">EOD</option></select>
          <input className="rounded-lg border border-gray-300 px-3 py-2" placeholder="Timezone" value={email.timezone || ''} onChange={e => setEmail({...email, timezone: e.target.value})} />
          <input type="time" className="rounded-lg border border-gray-300 px-3 py-2" value={email.morning_time} onChange={e => setEmail({...email, morning_time: e.target.value})} />
          <input type="time" className="rounded-lg border border-gray-300 px-3 py-2" value={email.eod_time} onChange={e => setEmail({...email, eod_time: e.target.value})} />
          <input className="md:col-span-2 rounded-lg border border-gray-300 px-3 py-2" placeholder="Jira CSV path for server scheduler" value={email.jira_csv_path || ''} onChange={e => setEmail({...email, jira_csv_path: e.target.value})} />
        </div>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!email.enabled} onChange={e => setEmail({...email, enabled: e.target.checked})} /> Enable automatic scheduled delivery</label>
        <div className="flex gap-3">
          <button onClick={saveEmail} className="btn-secondary">Save email settings</button>
          <button onClick={sendTestEmail} className="btn-primary">Send Test Email</button>
        </div>
        {emailMessage && <p className="text-sm text-gray-600">{emailMessage}</p>}
      </div>
    </div>
  )
}
