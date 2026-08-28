import StatusBadge from './StatusBadge'
import { getFileUrl } from '../api/client'

export default function BillCard({ bill, onClick }) {
  return (
    <div className="glass p-4 cursor-pointer hover:border-white/30 transition flex flex-col gap-2" onClick={() => onClick(bill.id)}>
      <div className="h-20 bg-black/20 rounded-lg flex items-center justify-center overflow-hidden">
        {bill.file_type === 'pdf' ? (
          <span className="text-xs text-red-400 font-bold">📄 PDF</span>
        ) : (
          <img src={getFileUrl(bill.id)} alt="bill" className="h-full w-full object-cover" />
        )}
      </div>
      <div className="flex justify-between items-start mt-1">
        <div>
          <p className="font-semibold text-sm truncate">{bill.vendor_name || (bill.status === 'PENDING' ? 'Extracting…' : 'Unknown')}</p>
          <p className="text-xs text-white/50">{bill.currency || ''} {bill.total_amount ? Number(bill.total_amount).toFixed(2) : '—'}</p>
        </div>
        <StatusBadge status={bill.status} />
      </div>
      <div className="text-[10px] text-white/30 flex justify-between">
        <span>{bill.llm_engine === 'gemini' ? '✨ Gemini' : '🦙 Ollama'}</span>
        <span>#{bill.id}</span>
      </div>
    </div>
  )
}
