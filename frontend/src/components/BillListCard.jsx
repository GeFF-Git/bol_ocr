import BillCard from './BillCard'

export default function BillListCard({ bills, onSelectBill }) {
  return (
    <div className="glass p-5 flex flex-col h-full">
      <h2 className="text-md font-bold mb-3">Recent Bills ({bills.length})</h2>
      <div className="flex-1 overflow-y-auto flex flex-col gap-2 max-h-[500px]">
        {bills.map(b => <BillCard key={b.id} bill={b} onClick={onSelectBill} />)}
      </div>
    </div>
  )
}
