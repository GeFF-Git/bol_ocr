import axios from 'axios'
const api = axios.create({ baseURL: 'http://localhost:8000' })

export async function uploadBill(file, llmEngine) {
  const form = new FormData()
  form.append('file', file)
  form.append('llm_engine', llmEngine)
  const res = await api.post('/api/bills/upload', form)
  return res.data
}
export async function listBills() {
  const res = await api.get('/api/bills')
  return res.data
}
export async function getBill(id) {
  const res = await api.get(`/api/bills/${id}`)
  return res.data
}
export async function updateBill(id, data) {
  const res = await api.put(`/api/bills/${id}`, data)
  return res.data
}
export function getFileUrl(id) {
  return `http://localhost:8000/api/bills/${id}/file`
}
