import { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import CaseFile from './components/CaseFile'
import { listDocuments } from './lib/api'

export default function App() {
  const [documents, setDocuments] = useState([])
  const [selectedId, setSelectedId] = useState(null)

  const refreshList = useCallback(async () => {
    try {
      const docs = await listDocuments()
      setDocuments(docs)
    } catch {
      // Backend not reachable yet - the sidebar's empty state covers
      // this silently; no need for a jarring error on first load.
    }
  }, [])

  useEffect(() => {
    refreshList()
    // Light polling so newly-finished background processing (from any
    // upload) eventually reflects in the sidebar's stamp badges too,
    // not just in the open case file.
    const id = setInterval(refreshList, 5000)
    return () => clearInterval(id)
  }, [refreshList])

  const handleUploaded = (result) => {
    setDocuments((docs) => [
      { file_id: result.file_id, filename: result.filename, processing_status: result.processing_status },
      ...docs,
    ])
    setSelectedId(result.file_id)
  }

  return (
    <div className="h-screen flex paper-texture">
      <Sidebar
        documents={documents}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onUploaded={handleUploaded}
      />
      {selectedId ? (
        <CaseFile key={selectedId} fileId={selectedId} />
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm font-mono" style={{ color: 'var(--color-ink-soft)' }}>
            Select a case file, or drop a document to begin.
          </p>
        </div>
      )}
    </div>
  )
}
