export default function StatCard({ icon, label, value }) {
  return (
    <div className="glass p-5 flex flex-col justify-between">
      <div className="flex justify-between items-center text-xs text-white/40 uppercase font-bold">
        <span>{label}</span>
        <span className="text-xl">{icon}</span>
      </div>
      <p className="text-3xl font-extrabold mt-3">{value}</p>
    </div>
  )
}
