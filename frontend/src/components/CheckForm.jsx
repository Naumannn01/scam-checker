import { useState } from 'react'

export default function CheckForm({ onSubmit, loading }) {
  const [inputValue, setInputValue] = useState('')
  const [messageText, setMessageText] = useState('')
  const [error, setError] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (!inputValue.trim()) {
      setError('Enter a URL, UPI ID, or phone number first.')
      return
    }
    setError('')
    onSubmit(inputValue.trim(), messageText.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="bg-slate-800 rounded-xl p-5">
      <label className="text-sm text-slate-400 block mb-1.5">URL, UPI ID, or phone number</label>
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        placeholder="paytm-refund-verify.tk"
        className="w-full mb-3 px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100 font-mono text-sm focus:outline-none focus:border-indigo-500"
      />

      <label className="text-sm text-slate-400 block mb-1.5">Message text (optional)</label>
      <textarea
        rows={2}
        value={messageText}
        onChange={(e) => setMessageText(e.target.value)}
        placeholder="Paste the accompanying message, if any"
        className="w-full mb-3 px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100 text-sm resize-y focus:outline-none focus:border-indigo-500"
      />

      <button
        type="submit"
        disabled={loading}
        className="w-full py-2.5 rounded-md bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors disabled:opacity-50"
      >
        {loading ? 'Checking...' : 'Check'}
      </button>

      {error && <p className="text-sm text-red-400 mt-2">{error}</p>}
    </form>
  )
}
