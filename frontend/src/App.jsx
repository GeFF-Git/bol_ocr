import { useState, useEffect, useCallback } from 'react'
import BentoGrid from './components/BentoGrid'
import BillDetailPanel from './components/BillDetailPanel'
import { listBills } from './api/client'

export default function App() {
  const [bills, setBills] = useState([])
  const [selectedBillId, setSelectedBillId] = useState(null)

  const refreshBills = useCallback(async () => {
    try {
      const data = await listBills()
      setBills(data)
    } catch (e) {}
  }, [])

  useEffect(() => {
    refreshBills()
    const id = setInterval(refreshBills, 3000)
    return () => clearInterval(id)
  }, [refreshBills])

  return (
    <div className="min-h-screen p-8 max-w-6xl mx-auto">
      <div className="mb-6 flex items-center gap-3">
        <span className="text-3xl">🧾</span>
        <h1 className="text-2xl font-bold text-white">AI Bill Processor</h1>
      </div>
      <BentoGrid bills={bills} onRefresh={refreshBills} onSelectBill={setSelectedBillId} />
      {selectedBillId && (
        <BillDetailPanel billId={selectedBillId} onClose={() => setSelectedBillId(null)} onSaved={() => { refreshBills(); setSelectedBillId(null); }} />
      )}
    </div>
  )
}
