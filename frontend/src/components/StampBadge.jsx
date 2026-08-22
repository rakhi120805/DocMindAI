/**
 * StampBadge — the signature visual element of this app.
 *
 * Deliberately styled like a real ink stamp (rotated slightly, rough
 * double-border, letter-spaced caps) rather than a generic colored
 * pill, because a rubber stamp is literally what a human verifier
 * would use on a physical document - it's the most characteristic
 * object in this app's actual subject matter, not a decorative choice.
 */
const VARIANTS = {
  verified: {
    label: 'VERIFIED',
    color: 'var(--color-verified)',
    bg: 'var(--color-verified-bg)',
  },
  warning: {
    label: 'WARNING',
    color: 'var(--color-warning)',
    bg: 'var(--color-warning-bg)',
  },
  risk: {
    label: 'HIGH RISK',
    color: 'var(--color-risk)',
    bg: 'var(--color-risk-bg)',
  },
  pending: {
    label: 'PROCESSING',
    color: 'var(--color-slate-dim)',
    bg: 'var(--color-paper-dim)',
  },
}

export default function StampBadge({ variant = 'pending', className = '' }) {
  const v = VARIANTS[variant] || VARIANTS.pending

  return (
    <span
      className={`inline-flex items-center px-3 py-1 text-xs font-semibold tracking-widest uppercase font-mono -rotate-2 select-none ${className}`}
      style={{
        color: v.color,
        backgroundColor: v.bg,
        border: `2px solid ${v.color}`,
        borderRadius: '3px',
        boxShadow: `0 0 0 1px ${v.bg}`,
      }}
    >
      {v.label}
    </span>
  )
}

/** Maps backend verification_status + risk_score to a stamp variant. */
export function variantFromStatus(verificationStatus, riskScore) {
  if (verificationStatus == null) return 'pending'
  if (riskScore != null && riskScore >= 50) return 'risk'
  if (verificationStatus === 'Warning') return 'warning'
  return 'verified'
}
