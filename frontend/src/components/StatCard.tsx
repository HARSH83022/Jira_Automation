interface Props {
  label: string
  value: string | number
  sub?: string
  color?: string
}

export default function StatCard({ label, value, sub, color = 'bg-brand-dark' }: Props) {
  return (
    <div className="card flex flex-col gap-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">{label}</p>
      <p className={`text-3xl font-bold text-gray-900`}>{value}</p>
      {sub && <p className="text-sm text-gray-500">{sub}</p>}
    </div>
  )
}
