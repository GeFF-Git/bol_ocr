import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { uploadBill, getBolByBillId } from '../api/client'

export default function UploadCard({ onUploadSuccess }) {
  const [engine, setEngine] = useState('gemini')
  const [docType, setDocType] = useState('bol')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [msg, setMsg] = useState(null)
  const navigate = useNavigate()

  const onDrop = useCallback(acc => { if (acc.length) { setFile(acc[0]); setMsg(null); } }, [])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: {'image/*': [], 'application/pdf': ['.pdf']}, maxFiles: 1 })

  const pollForBol = async (billId, retries = 20) => {
    for (let i = 0; i < retries; i++) {
      await new Promise(r => setTimeout(r, 3000))
      try {
        const bol = await getBolByBillId(billId)
        if (bol && bol.id) {
          navigate(`/bols/${bol.id}`)
          return
        }
      } catch (e) {
        // Not ready yet, keep polling
      }
    }
    setMsg({ type: 'err', text: 'Processing timed out. Check BOL History.' })
    setUploading(false)
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    try {
      const res = await uploadBill(file, engine, docType)
      setMsg({ type: 'ok', text: `Uploaded #${res.bill_id} — ${docType === 'bol' ? 'waiting for extraction…' : 'done!'}` })
      setFile(null)
      onUploadSuccess?.()
      if (docType === 'bol') {
        pollForBol(res.bill_id)
      } else {
        setUploading(false)
      }
    } catch(e) {
      setMsg({ type: 'err', text: e.message || 'Failed' })
      setUploading(false)
    }
  }

  return (
    <div className="glass p-6 flex flex-col gap-4">
      <h2 className="text-lg font-bold">Upload Document</h2>

      {/* Document Type Toggle */}
      <div className="flex gap-2 bg-white/[0.04] p-1 rounded-xl">
        {[{key: 'bol', label: '📋 Bill of Lading'}, {key: 'invoice', label: '🧾 Invoice'}].map(dt => (
          <button key={dt.key} onClick={() => setDocType(dt.key)} className={`flex-1 py-2 text-xs font-bold uppercase rounded-lg ${docType === dt.key ? 'bg-emerald-500 text-white' : 'text-white/40'}`}>
            {dt.label}
          </button>
        ))}
      </div>

      {/* LLM Engine Toggle */}
      <div className="flex gap-2 bg-white/[0.04] p-1 rounded-xl">
        {['ollama', 'gemini'].map(e => (
          <button key={e} onClick={() => setEngine(e)} className={`flex-1 py-2 text-xs font-bold uppercase rounded-lg ${engine === e ? 'bg-indigo-500 text-white' : 'text-white/40'}`}>
            {e === 'ollama' ? '🦙 Ollama' : '✨ Gemini'}
          </button>
        ))}
      </div>

      <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer ${isDragActive ? 'border-indigo-400' : 'border-white/10'}`}>
        <input {...getInputProps()} />
        {file ? <p className="text-indigo-300 font-bold">{file.name}</p> : <p className="text-white/40 text-sm">Drag & drop {docType === 'bol' ? 'BOL' : 'bill'} here or click</p>}
      </div>
      {msg && <p className={`text-xs ${msg.type === 'ok' ? 'text-emerald-400' : 'text-red-400'}`}>{msg.text}</p>}
      <button className="btn-primary" onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? 'Processing…' : `Process ${docType === 'bol' ? 'BOL' : 'Bill'}`}
      </button>
    </div>
  )
}

