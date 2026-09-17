import axios from 'axios'
const api = axios.create({ baseURL: 'http://localhost:8000' })

export async function uploadBill(file, llmEngine, docType = 'bol') {
  const form = new FormData()
  form.append('file', file)
  form.append('llm_engine', llmEngine)
  form.append('doc_type', docType)
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

export async function listBols() {
  const res = await api.get('/api/bols')
  return res.data
}
export async function getBol(id) {
  const res = await api.get(`/api/bols/${id}`)
  return res.data
}
export async function getBolByBillId(billId) {
  const res = await api.get(`/api/bols/by-bill/${billId}`)
  return res.data
}
export async function updateBol(id, data) {
  const res = await api.put(`/api/bols/${id}`, data)
  return res.data
}
