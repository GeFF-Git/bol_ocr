import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { uploadBill } from '../api/client'

export default function UploadCard({ onUploadSuccess }) {
  const [engine, setEngine] = useState('ollama')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [msg, setMsg] = useState(null)

  const onDrop = useCallback(acc => { if (acc.length) { setFile(acc[0]); setMsg(null); } }, [])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: {'image/*': [], 'application/pdf': ['.pdf']}, maxFiles: 1 })

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    try {
      const res = await uploadBill(file, engine)
      setMsg({ type: 'ok', text: `Uploaded Bill #${res.bill_id}!` })
      setFile(null)
      onUploadSuccess?.()
    } catch(e) {
      setMsg({ type: 'err', text: e.message || 'Failed' })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="glass p-6 flex flex-col gap-4">
      <h2 className="text-lg font-bold">Upload Bill</h2>
      <div className="flex gap-2 bg-white/[0.04] p-1 rounded-xl">
        {['ollama', 'gemini'].map(e => (
          <button key={e} onClick={() => setEngine(e)} className={`flex-1 py-2 text-xs font-bold uppercase rounded-lg ${engine === e ? 'bg-indigo-500 text-white' : 'text-white/40'}`}>
            {e === 'ollama' ? '🦙 Ollama' : '✨ Gemini'}
          </button>
        ))}
      </div>
      <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer ${isDragActive ? 'border-indigo-400' : 'border-white/10'}`}>
        <input {...getInputProps()} />
        {file ? <p className="text-indigo-300 font-bold">{file.name}</p> : <p className="text-white/40 text-sm">Drag & drop bill here or click</p>}
      </div>
      {msg && <p className={`text-xs ${msg.type === 'ok' ? 'text-emerald-400' : 'text-red-400'}`}>{msg.text}</p>}
      <button className="btn-primary" onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? 'Processing…' : 'Process Bill'}
      </button>
    </div>
  )
}
