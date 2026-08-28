import UploadCard from './UploadCard'
import BillListCard from './BillListCard'
import StatCard from './StatCard'

export default function BentoGrid({ bills, onRefresh, onSelectBill }) {
  const processed = bills.filter(b => ['PROCESSED', 'REVIEWED'].includes(b.status))
  const total = processed.reduce((s, b) => s + (parseFloat(b.total_amount) || 0), 0)

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="col-span-2 space-y-4">
        <UploadCard onUploadSuccess={onRefresh} />
        <div className="grid grid-cols-2 gap-4">
          <StatCard icon="📋" label="Processed" value={`${processed.length} / ${bills.length}`} />
          <StatCard icon="💰" label="Total Extracted" value={`$${total.toFixed(2)}`} />
        </div>
      </div>
      <div className="col-span-1">
        <BillListCard bills={bills} onSelectBill={onSelectBill} />
      </div>
    </div>
  )
}
