import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listBols } from '../api/client'
import StatusBadge from './StatusBadge'

export default function BolHistoryPage() {
  const [bols, setBols] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchBols = async () => {
      try {
        const data = await listBols()
        setBols(data)
      } catch (e) {
        console.error('Failed to load BOLs', e)
      } finally {
        setLoading(false)
      }
    }
    fetchBols()
    const id = setInterval(fetchBols, 5000)
    return () => clearInterval(id)
  }, [])

  if (loading) {
    return (
      <div className="glass p-12 text-center">
        <p className="text-white/50 animate-pulse">Loading BOL history…</p>
      </div>
    )
  }

  if (bols.length === 0) {
    return (
      <div className="glass p-12 text-center">
        <p className="text-4xl mb-3">📋</p>
        <p className="text-white/50">No Bills of Lading processed yet.</p>
        <p className="text-white/30 text-sm mt-1">Upload a BOL from the Dashboard to get started.</p>
      </div>
    )
  }

  return (
    <div className="glass p-6">
      <h2 className="text-xl font-bold mb-4">Bill of Lading History</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-white/40 text-xs uppercase border-b border-white/10">
              <th className="pb-3 pr-4">BOL No.</th>
              <th className="pb-3 pr-4">Shipper</th>
              <th className="pb-3 pr-4">Consignee</th>
              <th className="pb-3 pr-4">Vessel</th>
              <th className="pb-3 pr-4">Containers</th>
              <th className="pb-3 pr-4">Date</th>
              <th className="pb-3 pr-4">Status</th>
              <th className="pb-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {bols.map(bol => (
              <tr key={bol.id} className="border-b border-white/5 hover:bg-white/5 transition">
                <td className="py-3 pr-4 font-mono text-indigo-300">{bol.bol_number || '—'}</td>
                <td className="py-3 pr-4 max-w-[200px] truncate">{bol.shipper || '—'}</td>
                <td className="py-3 pr-4 max-w-[200px] truncate">{bol.consignee || '—'}</td>
                <td className="py-3 pr-4 text-white/60">{bol.vessel_voyage || '—'}</td>
                <td className="py-3 pr-4 text-center">{bol.containers?.length || 0}</td>
                <td className="py-3 pr-4 text-white/50">{bol.created_at ? new Date(bol.created_at).toLocaleDateString() : '—'}</td>
                <td className="py-3 pr-4"><StatusBadge status={bol.status || 'PENDING'} /></td>
                <td className="py-3">
                  <Link to={`/bols/${bol.id}`} className="btn-ghost text-xs px-3 py-1.5 inline-block hover:bg-white/10">Review →</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
