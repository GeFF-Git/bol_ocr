export default function StatusBadge({ status }) {
  const colors = {
    PENDING: 'bg-amber-400/20 text-amber-300 border-amber-400/30',
    PROCESSED: 'bg-emerald-400/20 text-emerald-300 border-emerald-400/30',
    FAILED: 'bg-red-400/20 text-red-300 border-red-400/30',
    REVIEWED: 'bg-blue-400/20 text-blue-300 border-blue-400/30',
  }
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${colors[status] || colors.PENDING}`}>
      {status}
    </span>
  )
}
