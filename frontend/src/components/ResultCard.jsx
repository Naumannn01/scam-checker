import VerdictBadge from './VerdictBadge'

function explainDetails(details) {
  const reasons = []

  if (details.blocklist_hit) {
    reasons.push(`Matches a known phishing URL (source: ${details.blocklist_source})`)
  }
  if (details.domain_age_days !== undefined && details.domain_age_days !== null) {
    reasons.push(`Domain registered ${details.domain_age_days} days ago`)
  } else if (details.whois_error) {
    reasons.push('No WHOIS registration data found')
  }
  if (details.message_analysis) {
    const ma = details.message_analysis
    if (ma.urgency_keyword_hits?.length > 0) {
      reasons.push(`Message uses pressure-tactic language (${ma.urgency_keyword_hits.join(', ')})`)
    }
    if (ma.caps_ratio > 0.3) {
      reasons.push('Message uses excessive capitalization')
    }
  }
  if (reasons.length === 0) {
    reasons.push('No suspicious patterns detected')
  }
  return reasons
}

export default function ResultCard({ entry }) {
  if (!entry) return null
  const reasons = explainDetails(entry.details || {})

  return (
    <div className="bg-slate-800 rounded-xl p-5 mt-4 animate-[fadeIn_0.3s_ease-in]">
      <div className="flex items-center gap-3 mb-4">
        <VerdictBadge verdict={entry.verdict} size="lg" />
        <span className="text-sm text-slate-400">Risk score {entry.risk_score?.toFixed(2)}</span>
      </div>
      <div className="border-t border-slate-700 pt-3">
        <p className="text-sm text-slate-400 mb-2">Why</p>
        <ul className="space-y-1.5">
          {reasons.map((r, i) => (
            <li key={i} className="text-sm text-slate-200 flex gap-2">
              <span className="text-slate-600 mt-1.5">•</span>
              <span>{r}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
