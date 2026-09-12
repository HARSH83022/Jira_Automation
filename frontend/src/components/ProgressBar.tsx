interface Props { value: number; max?: number; color?: string }

export default function ProgressBar({ value, max = 100, color = 'bg-brand-mid' }: Props) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className={`${color} h-2 rounded-full transition-all duration-500`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}
