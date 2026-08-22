import StampBadge, { variantFromStatus } from './StampBadge'
import UploadSlot from './UploadSlot'

export default function Sidebar({ documents, selectedId, onSelect, onUploaded }) {
  return (
    <aside
      className="w-80 shrink-0 h-full flex flex-col border-r"
      style={{ borderColor: 'var(--color-manila)' }}
    >
      <div className="p-5 border-b" style={{ borderColor: 'var(--color-manila)' }}>
        <h1 className="font-serif text-2xl" style={{ fontFamily: 'var(--font-display)' }}>
          DocMind
        </h1>
        <p className="text-xs font-mono mt-1" style={{ color: 'var(--color-ink-soft)' }}>
          Document intake &amp; verification
        </p>
      </div>

      <div className="p-5 border-b" style={{ borderColor: 'var(--color-manila)' }}>
        <UploadSlot onUploaded={onUploaded} />
      </div>

      <div className="flex-1 overflow-y-auto">
        {documents.length === 0 ? (
          <p className="p-5 text-xs font-mono" style={{ color: 'var(--color-ink-soft)' }}>
            No case files yet. Drop a document above to start one.
          </p>
        ) : (
          <ul>
            {documents.map((doc) => (
              <li key={doc.file_id}>
                <button
                  onClick={() => onSelect(doc.file_id)}
                  className={`w-full text-left px-5 py-3 border-b transition-colors flex flex-col gap-1.5 ${
                    selectedId === doc.file_id ? 'bg-white' : 'hover:bg-white/60'
                  }`}
                  style={{
                    borderColor: 'var(--color-paper-dim)',
                    borderLeft: selectedId === doc.file_id ? '3px solid var(--color-manila-dark)' : '3px solid transparent',
                  }}
                >
                  <span className="text-sm font-medium truncate" style={{ color: 'var(--color-ink)' }}>
                    {doc.filename}
                  </span>
                  <div className="flex items-center gap-2">
                    <StampBadge
                      variant={
                        doc.processing_status === 'failed'
                          ? 'risk'
                          : doc.processing_status !== 'done'
                          ? 'pending'
                          : variantFromStatus(doc.verification_status, doc.risk_score)
                      }
                      className="!px-2 !py-0.5 !text-[10px] !rotate-0"
                    />
                    {doc.document_type && (
                      <span className="text-xs font-mono" style={{ color: 'var(--color-slate-dim)' }}>
                        {doc.document_type}
                      </span>
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  )
}
