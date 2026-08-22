export default function RiskMeter({ score }) {
  if (score == null) return null
  const color =
    score >= 50 ? 'var(--color-risk)' : score >= 20 ? 'var(--color-warning)' : 'var(--color-verified)'

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-paper-dim)' }}>
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${score}%`, backgroundColor: color }}
        />
      </div>
      <span className="font-mono text-sm font-medium" style={{ color }}>
        {score}/100
      </span>
    </div>
  )
}
