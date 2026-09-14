import VerdictBadge from './VerdictBadge'

export default function HistoryList({ entries }) {
  if (!entries || entries.length === 0) return null

  return (
    <div className="mt-8">
      <p className="text-sm text-slate-400 mb-2">Recent checks</p>
      <div className="divide-y divide-slate-800">
        {entries.map((e) => (
          <div key={e.id} className="flex items-center justify-between py-2.5">
            <span className="font-mono text-sm text-slate-200 truncate max-w-[400px]">{e.input_value}</span>
            <VerdictBadge verdict={e.verdict} />
          </div>
        ))}
      </div>
    </div>
  )
}
