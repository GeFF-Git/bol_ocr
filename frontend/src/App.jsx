import { useState, useEffect, useCallback } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import BentoGrid from './components/BentoGrid'
import BillDetailPanel from './components/BillDetailPanel'
import BolHistoryPage from './components/BolHistoryPage'
import BolReviewPage from './components/BolReviewPage'
import { listBills } from './api/client'

function Dashboard({ bills, onRefresh, onSelectBill, selectedBillId, setSelectedBillId }) {
  return (
    <>
      <BentoGrid bills={bills} onRefresh={onRefresh} onSelectBill={onSelectBill} />
      {selectedBillId && (
        <BillDetailPanel billId={selectedBillId} onClose={() => setSelectedBillId(null)} onSaved={() => { onRefresh(); setSelectedBillId(null); }} />
      )}
    </>
  )
}

export default function App() {
  const [bills, setBills] = useState([])
  const [selectedBillId, setSelectedBillId] = useState(null)
  const location = useLocation()

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
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🧾</span>
          <h1 className="text-2xl font-bold text-white">AI Bill Processor</h1>
        </div>
        <nav className="flex gap-2">
          <Link to="/" className={`btn-ghost text-sm ${location.pathname === '/' ? 'bg-white/10 text-white' : ''}`}>Dashboard</Link>
          <Link to="/bols" className={`btn-ghost text-sm ${location.pathname.startsWith('/bols') ? 'bg-white/10 text-white' : ''}`}>📋 BOL History</Link>
        </nav>
      </div>
      <Routes>
        <Route path="/" element={
          <Dashboard bills={bills} onRefresh={refreshBills} onSelectBill={setSelectedBillId} selectedBillId={selectedBillId} setSelectedBillId={setSelectedBillId} />
        } />
        <Route path="/bols" element={<BolHistoryPage />} />
        <Route path="/bols/:bolId" element={<BolReviewPage />} />
      </Routes>
    </div>
  )
}

