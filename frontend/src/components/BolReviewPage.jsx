import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getBol, updateBol, getFileUrl } from '../api/client'
import StatusBadge from './StatusBadge'

const EMPTY_CONTAINER = {
  container_number: '',
  seal_number: '',
  marks_and_numbers: '',
  description: '',
  gross_cargo_weight: '',
  measurement: '',
}

export default function BolReviewPage() {
  const { bolId } = useParams()
  const navigate = useNavigate()
  const [bol, setBol] = useState(null)
  const [form, setForm] = useState({})
  const [containers, setContainers] = useState([])
  const [notifyParties, setNotifyParties] = useState([])
  const [newParty, setNewParty] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchBol = async () => {
      try {
        const data = await getBol(bolId)
        setBol(data)
        setForm(data)
        setContainers(data.containers || [])
        setNotifyParties(data.notify_parties || [])
      } catch (e) {
        console.error('Failed to load BOL', e)
      } finally {
        setLoading(false)
      }
    }
    fetchBol()
  }, [bolId])

  const updateField = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  const updateContainer = (index, field, value) => {
    setContainers(prev => prev.map((c, i) => i === index ? { ...c, [field]: value } : c))
  }

  const addContainer = () => {
    setContainers(prev => [...prev, { ...EMPTY_CONTAINER }])
  }

  const removeContainer = (index) => {
    setContainers(prev => prev.filter((_, i) => i !== index))
  }

  const addNotifyParty = () => {
    const trimmed = newParty.trim()
    if (trimmed) {
      setNotifyParties(prev => [...prev, trimmed])
      setNewParty('')
    }
  }

  const removeNotifyParty = (index) => {
    setNotifyParties(prev => prev.filter((_, i) => i !== index))
  }

  const handleSave = async () => {
    setSaving(true)
    setSaveMsg(null)
    try {
      const payload = {
        bol_number: form.bol_number || null,
        shipper: form.shipper || null,
        consignee: form.consignee || null,
        notify_parties: notifyParties,
        discharge_agent: form.discharge_agent || null,
        vessel_voyage: form.vessel_voyage || null,
        port_of_loading: form.port_of_loading || null,
        place_of_receipt: form.place_of_receipt || null,
        booking_ref: form.booking_ref || null,
        port_of_discharge: form.port_of_discharge || null,
        place_of_delivery: form.place_of_delivery || null,
        shipped_on_board_date: form.shipped_on_board_date || null,
        containers: containers.map(c => ({
          container_number: c.container_number || null,
          seal_number: c.seal_number || null,
          marks_and_numbers: c.marks_and_numbers || null,
          description: c.description || null,
          gross_cargo_weight: c.gross_cargo_weight || null,
          measurement: c.measurement || null,
        })),
      }
      const updated = await updateBol(bolId, payload)
      setBol(updated)
      setSaveMsg({ type: 'ok', text: 'Saved successfully!' })
      setTimeout(() => setSaveMsg(null), 3000)
    } catch (e) {
      setSaveMsg({ type: 'err', text: e?.response?.data?.detail || e.message || 'Save failed' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="glass p-12 text-center">
        <p className="text-white/50 animate-pulse">Loading BOL…</p>
      </div>
    )
  }

  if (!bol) {
    return (
      <div className="glass p-12 text-center">
        <p className="text-red-400">BOL not found.</p>
        <button className="btn-ghost mt-4" onClick={() => navigate('/bols')}>← Back to History</button>
      </div>
    )
  }

  const isRequired = (val) => !val || val.trim() === ''

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button className="btn-ghost text-sm" onClick={() => navigate('/bols')}>← Back</button>
          <h2 className="text-xl font-bold">BOL Review: {form.bol_number || `#${bol.id}`}</h2>
          <StatusBadge status={bol.status || 'PENDING'} />
        </div>
        <div className="flex items-center gap-3">
          {saveMsg && (
            <span className={`text-xs ${saveMsg.type === 'ok' ? 'text-emerald-400' : 'text-red-400'}`}>{saveMsg.text}</span>
          )}
          <button className="btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Main content: image + fields */}
      <div className="flex gap-4" style={{ minHeight: '600px' }}>
        {/* Left: Document viewer */}
        {bol.bill_id && (
          <div className="w-2/5 glass p-3 overflow-auto">
            {bol.file_type === 'pdf' ? (
              <embed src={getFileUrl(bol.bill_id)} type="application/pdf" className="w-full h-full min-h-[600px]" />
            ) : (
              <img src={getFileUrl(bol.bill_id)} alt="BOL document" className="w-full object-contain" />
            )}
          </div>
        )}

        {/* Right: Editable fields */}
        <div className={`${bol.bill_id ? 'w-3/5' : 'w-full'} glass p-5 overflow-y-auto space-y-4`}>
          <h3 className="text-sm font-bold text-white/60 uppercase">BOL Details</h3>

          {/* Row 1: BOL Number, Booking Ref */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/40 block mb-1">Bill of Lading No. *</label>
              <input className={`glass-input ${isRequired(form.bol_number) ? 'border-amber-400/50' : ''}`}
                value={form.bol_number || ''}
                onChange={e => updateField('bol_number', e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1">Booking Ref.</label>
              <input className="glass-input" value={form.booking_ref || ''}
                onChange={e => updateField('booking_ref', e.target.value)} />
            </div>
          </div>

          {/* Row 2: Shipper (full width) */}
          <div>
            <label className="text-xs text-white/40 block mb-1">Shipper *</label>
            <textarea rows={2} className={`glass-input ${isRequired(form.shipper) ? 'border-amber-400/50' : ''}`}
              value={form.shipper || ''}
              onChange={e => updateField('shipper', e.target.value)} />
          </div>

          {/* Row 3: Consignee (full width) */}
          <div>
            <label className="text-xs text-white/40 block mb-1">Consignee</label>
            <textarea rows={2} className="glass-input" value={form.consignee || ''}
              onChange={e => updateField('consignee', e.target.value)} />
          </div>

          {/* Row 4: Notify Parties (tag input) */}
          <div>
            <label className="text-xs text-white/40 block mb-1">Notify Parties</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {notifyParties.map((party, i) => (
                <span key={i} className="bg-white/10 px-3 py-1 rounded-full text-xs flex items-center gap-1.5">
                  {party}
                  <button onClick={() => removeNotifyParty(i)} className="text-white/40 hover:text-red-400">×</button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input className="glass-input flex-1" placeholder="Add notify party…" value={newParty}
                onChange={e => setNewParty(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addNotifyParty())} />
              <button className="btn-ghost text-xs" onClick={addNotifyParty}>Add</button>
            </div>
          </div>

          {/* Row 5: Discharge Agent (full width) */}
          <div>
            <label className="text-xs text-white/40 block mb-1">Port of Discharge Agent</label>
            <textarea rows={2} className="glass-input" value={form.discharge_agent || ''}
              onChange={e => updateField('discharge_agent', e.target.value)} />
          </div>

          {/* Row 6: Vessel, Shipped on Board Date */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/40 block mb-1">Vessel & Voyage No.</label>
              <input className="glass-input" value={form.vessel_voyage || ''}
                onChange={e => updateField('vessel_voyage', e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1">Shipped on Board Date</label>
              <input type="date" className="glass-input" value={form.shipped_on_board_date || ''}
                onChange={e => updateField('shipped_on_board_date', e.target.value)} />
            </div>
          </div>

          {/* Row 7: Port of Loading, Place of Receipt */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/40 block mb-1">Port of Loading</label>
              <input className="glass-input" value={form.port_of_loading || ''}
                onChange={e => updateField('port_of_loading', e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1">Place of Receipt</label>
              <input className="glass-input" value={form.place_of_receipt || ''}
                onChange={e => updateField('place_of_receipt', e.target.value)} />
            </div>
          </div>

          {/* Row 8: Port of Discharge, Place of Delivery */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/40 block mb-1">Port of Discharge</label>
              <input className="glass-input" value={form.port_of_discharge || ''}
                onChange={e => updateField('port_of_discharge', e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1">Place of Delivery</label>
              <input className="glass-input" value={form.place_of_delivery || ''}
                onChange={e => updateField('place_of_delivery', e.target.value)} />
            </div>
          </div>
        </div>
      </div>

      {/* Containers Section */}
      <div className="glass p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-white/60 uppercase">Containers ({containers.length})</h3>
          <button className="btn-ghost text-xs" onClick={addContainer}>+ Add Container</button>
        </div>

        {containers.length === 0 ? (
          <p className="text-white/30 text-sm text-center py-4">No containers. Click "+ Add Container" to add one.</p>
        ) : (
          <div className="space-y-3">
            {containers.map((c, i) => (
              <div key={i} className="bg-white/[0.03] border border-white/10 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-white/50">Container {i + 1}</span>
                  <button className="text-xs text-red-400/70 hover:text-red-400" onClick={() => removeContainer(i)}>Remove</button>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Container No.</label>
                    <input className="glass-input" value={c.container_number || ''}
                      onChange={e => updateContainer(i, 'container_number', e.target.value)} />
                  </div>
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Seal No.</label>
                    <input className="glass-input" value={c.seal_number || ''}
                      onChange={e => updateContainer(i, 'seal_number', e.target.value)} />
                  </div>
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Marks & Numbers</label>
                    <input className="glass-input" value={c.marks_and_numbers || ''}
                      onChange={e => updateContainer(i, 'marks_and_numbers', e.target.value)} />
                  </div>
                  <div className="col-span-3">
                    <label className="text-xs text-white/40 block mb-1">Description of Packages and Goods</label>
                    <textarea rows={2} className="glass-input" value={c.description || ''}
                      onChange={e => updateContainer(i, 'description', e.target.value)} />
                  </div>
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Gross Cargo Weight</label>
                    <input className="glass-input" value={c.gross_cargo_weight || ''}
                      onChange={e => updateContainer(i, 'gross_cargo_weight', e.target.value)} />
                  </div>
                  <div>
                    <label className="text-xs text-white/40 block mb-1">Measurement</label>
                    <input className="glass-input" value={c.measurement || ''}
                      onChange={e => updateContainer(i, 'measurement', e.target.value)} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
