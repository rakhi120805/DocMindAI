import { useState } from 'react'
import { useDocumentStatus } from '../lib/useDocumentStatus'
import StampBadge, { variantFromStatus } from './StampBadge'
import RiskMeter from './RiskMeter'
import AskPanel from './AskPanel'

const TABS = ['Overview', 'Extracted Data', 'Verification', 'Ask']

export default function CaseFile({ fileId }) {
  const { status, loading, pollError } = useDocumentStatus(fileId)
  const [tab, setTab] = useState('Overview')

  if (loading && !status) {
    return <EmptyState message="Opening case file…" />
  }
  if (pollError) {
    return <EmptyState message={`Couldn't reach the backend: ${pollError.message}`} tone="risk" />
  }
  if (!status) return null

  const isProcessing = status.processing_status === 'processing' || status.processing_status === 'queued'
  const isFailed = status.processing_status === 'failed'

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <div className="px-8 py-6 border-b" style={{ borderColor: 'var(--color-manila)' }}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl" style={{ fontFamily: 'var(--font-display)' }}>
              {status.filename}
            </h2>
            <p className="text-xs font-mono mt-1" style={{ color: 'var(--color-ink-soft)' }}>
              {status.file_id}
            </p>
          </div>
          <StampBadge
            variant={
              isFailed ? 'risk' : isProcessing ? 'pending' : variantFromStatus(status.verification_status, status.risk_score)
            }
          />
        </div>

        {isProcessing && (
          <p className="mt-3 text-sm font-mono animate-pulse" style={{ color: 'var(--color-slate)' }}>
            Working through the pipeline — OCR, classification, extraction, verification&hellip;
          </p>
        )}
        {isFailed && (
          <p className="mt-3 text-sm font-mono" style={{ color: 'var(--color-risk)' }}>
            {status.error || 'Processing failed for an unknown reason.'}
          </p>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b px-8" style={{ borderColor: 'var(--color-manila)' }}>
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="px-4 py-3 text-sm font-medium -mb-px border-b-2 transition-colors"
            style={{
              borderColor: tab === t ? 'var(--color-manila-dark)' : 'transparent',
              color: tab === t ? 'var(--color-ink)' : 'var(--color-ink-soft)',
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {tab === 'Overview' && <OverviewTab status={status} />}
        {tab === 'Extracted Data' && <ExtractedDataTab status={status} />}
        {tab === 'Verification' && <VerificationTab status={status} />}
        {tab === 'Ask' && <AskPanel fileId={fileId} disabled={status.processing_status !== 'done'} />}
      </div>
    </div>
  )
}

function OverviewTab({ status }) {
  if (status.processing_status !== 'done') {
    return <p className="text-sm font-mono" style={{ color: 'var(--color-ink-soft)' }}>Overview will appear once processing finishes.</p>
  }
  return (
    <div className="max-w-md space-y-6">
      <Field label="Document type">
        <span className="text-lg" style={{ fontFamily: 'var(--font-display)' }}>{status.document_type || 'Unclassified'}</span>
      </Field>
      <Field label="Classification confidence">
        <span className="font-mono">{status.classification_confidence != null ? status.classification_confidence.toFixed(2) : '—'}</span>
      </Field>
      <Field label="Risk score">
        <RiskMeter score={status.risk_score} />
      </Field>
    </div>
  )
}

function ExtractedDataTab({ status }) {
  const fields = status.extracted_metadata || {}
  const entries = Object.entries(fields)

  if (status.processing_status !== 'done') {
    return <p className="text-sm font-mono" style={{ color: 'var(--color-ink-soft)' }}>Extracted data will appear once processing finishes.</p>
  }
  if (entries.length === 0) {
    return <p className="text-sm font-mono" style={{ color: 'var(--color-ink-soft)' }}>No fields were extracted for this document type.</p>
  }

  return (
    <table className="w-full max-w-xl text-sm font-mono border-collapse">
      <tbody>
        {entries.map(([key, value]) => (
          <tr key={key} className="border-b" style={{ borderColor: 'var(--color-paper-dim)' }}>
            <td className="py-2 pr-4 align-top" style={{ color: 'var(--color-ink-soft)' }}>{key}</td>
            <td className="py-2" style={{ color: value == null ? 'var(--color-ink-soft)' : 'var(--color-ink)' }}>
              {value == null ? 'null' : String(value)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function VerificationTab({ status }) {
  if (status.processing_status !== 'done') {
    return <p className="text-sm font-mono" style={{ color: 'var(--color-ink-soft)' }}>Verification results will appear once processing finishes.</p>
  }
  const issues = status.verification_issues || []

  if (issues.length === 0) {
    return (
      <div className="flex items-center gap-3">
        <StampBadge variant="verified" />
        <p className="text-sm" style={{ color: 'var(--color-ink-soft)' }}>No issues found during verification.</p>
      </div>
    )
  }

  return (
    <ul className="space-y-2 max-w-lg">
      {issues.map((issue, i) => (
        <li
          key={i}
          className="text-sm font-mono px-3 py-2 rounded-sm border"
          style={{ color: 'var(--color-warning)', backgroundColor: 'var(--color-warning-bg)', borderColor: 'var(--color-warning)' }}
        >
          {issue}
        </li>
      ))}
    </ul>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <p className="text-xs font-mono uppercase tracking-widest mb-1.5" style={{ color: 'var(--color-slate-dim)' }}>
        {label}
      </p>
      {children}
    </div>
  )
}

function EmptyState({ message, tone = 'default' }) {
  return (
    <div className="flex-1 flex items-center justify-center">
      <p
        className="text-sm font-mono"
        style={{ color: tone === 'risk' ? 'var(--color-risk)' : 'var(--color-ink-soft)' }}
      >
        {message}
      </p>
    </div>
  )
}
