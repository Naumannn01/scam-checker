import { ShieldCheck, AlertTriangle, AlertOctagon, HelpCircle } from 'lucide-react'

const meta = {
  safe: { label: 'Safe', bg: 'bg-emerald-500/15', text: 'text-emerald-400', icon: ShieldCheck },
  suspicious: { label: 'Suspicious', bg: 'bg-amber-500/15', text: 'text-amber-400', icon: AlertTriangle },
  high_risk: { label: 'High risk', bg: 'bg-red-500/15', text: 'text-red-400', icon: AlertOctagon },
  unknown: { label: 'Checking...', bg: 'bg-slate-500/15', text: 'text-slate-400', icon: HelpCircle },
}

export default function VerdictBadge({ verdict, size = 'sm' }) {
  const m = meta[verdict] || meta.unknown
  const Icon = m.icon
  const textSize = size === 'lg' ? 'text-base' : 'text-xs'
  const padding = size === 'lg' ? 'px-3 py-1.5' : 'px-2.5 py-1'

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md font-medium ${m.bg} ${m.text} ${textSize} ${padding}`}>
      <Icon size={size === 'lg' ? 16 : 14} />
      {m.label}
    </span>
  )
}
