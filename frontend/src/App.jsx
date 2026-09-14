import { useState, useEffect, useRef } from 'react'
import CheckForm from './components/CheckForm'
import ResultCard from './components/ResultCard'
import HistoryList from './components/HistoryList'
import { submitCheck, getCheck, getHistory } from './api'

export default function App() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const pollRef = useRef(null)

  useEffect(() => {
    loadHistory()
    return () => clearTimeout(pollRef.current)
  }, [])

  async function loadHistory() {
    try {
      const data = await getHistory(4)
      setHistory(data)
    } catch (err) {
      console.error('Failed to load history:', err)
    }
  }

  async function handleSubmit(inputValue, messageText) {
    setLoading(true)
    setResult(null)

    try {
      const entry = await submitCheck(inputValue, messageText)
      pollForResult(entry.id)
    } catch (err) {
      setLoading(false)
      if (err.response?.status === 429) {
        alert('Too many checks — please wait a minute and try again.')
      } else {
        alert('Something went wrong. Please try again.')
      }
      console.error(err)
    }
  }

  function pollForResult(id, attempt = 0) {
    if (attempt > 15) {
      setLoading(false)
      alert('This is taking longer than expected. Check history in a moment.')
      return
    }

    pollRef.current = setTimeout(async () => {
      try {
        const entry = await getCheck(id)
        if (entry.verdict !== 'unknown') {
          setResult(entry)
          setLoading(false)
          loadHistory()
        } else {
          pollForResult(id, attempt + 1)
        }
      } catch (err) {
        setLoading(false)
        console.error(err)
      }
    }, 2000)
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <div className="max-w-xl mx-auto px-4 py-10">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-base font-medium">Scam checker</h1>
          </div>
          <p className="text-sm text-slate-400 mb-1 leading-relaxed">
            Paste a link, UPI ID, or phone number before you trust it. Every check
            runs against live threat data and plain-language reasoning, not guesswork.
          </p>
          <p className="text-sm font-medium text-indigo-400">Stay alert. Stay safe.</p>
        </div>

        <CheckForm onSubmit={handleSubmit} loading={loading} />

        {loading && (
          <div className="flex items-center gap-2 pt-4 text-sm text-slate-400">
            <span className="animate-spin inline-block w-4 h-4 border-2 border-slate-600 border-t-indigo-400 rounded-full" />
            Running checks
          </div>
        )}

        {result && <ResultCard entry={result} />}

        <HistoryList entries={history} />
      </div>
    </div>
  )
}