import axios from 'axios'

const API_BASE = 'http://localhost:8000'

export async function submitCheck(inputValue, messageText) {
  const res = await axios.post(`${API_BASE}/check`, {
    input_value: inputValue,
    message_text: messageText || null,
  })
  return res.data
}

export async function getCheck(id) {
  const res = await axios.get(`${API_BASE}/check/${id}`)
  return res.data
}

export async function getHistory(limit = 4) {
  const res = await axios.get(`${API_BASE}/check/history`, {
    params: { limit },
  })
  return res.data
}