export default function StatCard({ 
  icon: Icon, 
  title, 
  value, 
  subtext, 
  subtextColor = "text-gray-500", 
  iconBg = "bg-gray-50", 
  iconColor = "text-gray-500" 
}) {
  return (
    <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100 flex items-center gap-5">
      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${iconBg}`}>
        <Icon className={`w-6 h-6 ${iconColor}`} />
      </div>
      <div>
        <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">{title}</p>
        <div className="text-2xl font-bold text-gray-900 leading-none mb-1">{value}</div>
        {subtext && <p className={`text-xs font-medium ${subtextColor}`}>{subtext}</p>}
      </div>
    </div>
  );
}