import { useState } from 'react'
import { queryDocument } from '../lib/api'

export default function AskPanel({ fileId, disabled }) {
  const [question, setQuestion] = useState('')
  const [history, setHistory] = useState([]) // [{question, answer, confidence, latency_ms, error}]
  const [asking, setAsking] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    const q = question.trim()
    if (!q || asking) return

    setAsking(true)
    setQuestion('')
    try {
      const result = await queryDocument(fileId, q)
      setHistory((h) => [...h, { question: q, ...result }])
    } catch (err) {
      setHistory((h) => [...h, { question: q, error: err.detail || err.message }])
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {history.length === 0 && (
          <p className="text-sm font-mono" style={{ color: 'var(--color-ink-soft)' }}>
            Ask anything grounded in this document — e.g. "What is the total amount?"
          </p>
        )}
        {history.map((turn, i) => (
          <div key={i} className="space-y-1.5">
            <p className="text-sm font-medium" style={{ color: 'var(--color-slate)' }}>
              {turn.question}
            </p>
            {turn.error ? (
              <p className="text-sm font-mono" style={{ color: 'var(--color-risk)' }}>
                {turn.error}
              </p>
            ) : (
              <div
                className="rounded-sm p-3 border"
                style={{ backgroundColor: 'var(--color-paper-dim)', borderColor: 'var(--color-paper-dim)' }}
              >
                <p className="text-sm">{turn.answer}</p>
                <div className="flex items-center gap-3 mt-2 text-[11px] font-mono" style={{ color: 'var(--color-slate-dim)' }}>
                  <span>confidence {(turn.confidence ?? 0).toFixed(2)}</span>
                  <span>&middot;</span>
                  <span>{turn.latency_ms}ms</span>
                </div>
              </div>
            )}
          </div>
        ))}
        {asking && (
          <p className="text-sm font-mono animate-pulse" style={{ color: 'var(--color-ink-soft)' }}>
            Reading the case file&hellip;
          </p>
        )}
      </div>

      <form onSubmit={submit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={disabled || asking}
          placeholder={disabled ? 'Waiting for processing to finish…' : 'Ask a question about this document'}
          className="flex-1 px-3 py-2 text-sm rounded-sm border outline-none focus:ring-2"
          style={{ borderColor: 'var(--color-manila)', backgroundColor: 'white' }}
        />
        <button
          type="submit"
          disabled={disabled || asking || !question.trim()}
          className="px-4 py-2 text-sm font-medium rounded-sm text-white disabled:opacity-40"
          style={{ backgroundColor: 'var(--color-slate)' }}
        >
          Ask
        </button>
      </form>
    </div>
  )
}
