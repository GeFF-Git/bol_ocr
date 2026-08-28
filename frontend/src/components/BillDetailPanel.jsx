import { useState, useEffect } from 'react'
import { getBill, updateBill, getFileUrl } from '../api/client'
import StatusBadge from './StatusBadge'

export default function BillDetailPanel({ billId, onClose, onSaved }) {
  const [bill, setBill] = useState(null)
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getBill(billId).then(d => { setBill(d); setForm(d || {}); })
  }, [billId])

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateBill(billId, form)
      onSaved?.()
    } finally {
      setSaving(false)
    }
  }

  if (!bill) return null

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex justify-end">
      <div className="w-full max-w-4xl glass m-4 flex flex-col p-6 overflow-hidden">
        <div className="flex justify-between items-center pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold">Bill #{bill.id}</h2>
            <StatusBadge status={bill.status} />
          </div>
          <button className="btn-ghost" onClick={onClose}>✕</button>
        </div>

        <div className="flex-1 flex gap-4 overflow-hidden py-4">
          <div className="w-1/2 overflow-auto bg-black/30 rounded-xl p-2">
            {bill.file_type === 'pdf' ? (
              <embed src={getFileUrl(bill.id)} type="application/pdf" className="w-full h-full min-h-[400px]" />
            ) : (
              <img src={getFileUrl(bill.id)} alt="bill" className="w-full object-contain" />
            )}
          </div>
          <div className="w-1/2 overflow-y-auto space-y-3 pr-2">
            <div>
              <label className="text-xs text-white/40 block mb-1">Vendor Name</label>
              <input className="glass-input" value={form.vendor_name || ''} onChange={e => setForm({...form, vendor_name: e.target.value})} />
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1">Invoice Number</label>
              <input className="glass-input" value={form.invoice_number || ''} onChange={e => setForm({...form, invoice_number: e.target.value})} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-white/40 block mb-1">Date</label>
                <input type="date" className="glass-input" value={form.invoice_date || ''} onChange={e => setForm({...form, invoice_date: e.target.value})} />
              </div>
              <div>
                <label className="text-xs text-white/40 block mb-1">Total Amount</label>
                <input type="number" step="0.01" className="glass-input" value={form.total_amount || ''} onChange={e => setForm({...form, total_amount: parseFloat(e.target.value) || 0})} />
              </div>
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1">Notes</label>
              <textarea rows={3} className="glass-input" value={form.notes || ''} onChange={e => setForm({...form, notes: e.target.value})} />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-white/10 flex justify-end gap-2">
          <button className="btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save & Mark Reviewed'}
          </button>
        </div>
      </div>
    </div>
  )
}
