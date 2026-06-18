import api from './api'
import type { Analysis } from '@/types'

export const analysisService = {
  start: (docId: number, force = false) =>
    api.post<Analysis>(`/analysis/${docId}/start`, null, { params: force ? { force: true } : {} }).then((r) => r.data),

  get: (docId: number) =>
    api.get<Analysis>(`/analysis/${docId}`).then((r) => r.data),

  delete: (docId: number) => api.delete(`/analysis/${docId}`),

  downloadReport: (docId: number, filename?: string) =>
    api.get(`/reports/${docId}/pdf`, { responseType: 'blob' }).then((r) => {
      const disposition = r.headers['content-disposition'] || ''
      const serverName = disposition.match(/filename="?([^";\n]+)"?/)?.[1]
      const url = URL.createObjectURL(new Blob([r.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = serverName || filename || `analiz_${docId}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }),

  getReferenceContractDetail: (docId: number | string) =>
    api.get(`/admin/reference-contracts/${docId}`).then((r) => r.data),

  downloadReferenceContract: async (docId: number | string, filename?: string) => {
    const response = await api.get(`/admin/reference-contracts/${docId}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([response.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = filename || `reference_${docId}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },
}

export const adminService = {
  listUsers: () => api.get('/admin/users').then((r) => r.data),

  listReferenceContracts: (page = 1, size = 20) =>
    api.get('/admin/reference-contracts', { params: { page, size } }).then((r) => r.data),

  uploadReferenceContract: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/admin/reference-contracts', fd).then((r) => r.data)
  },

  retryReferenceContract: (id: number) =>
    api.post(`/admin/reference-contracts/${id}/retry`).then((r) => r.data),

  deleteReferenceContract: (id: number) => api.delete(`/admin/reference-contracts/${id}`),

  getTTKStatus: () => api.get('/admin/ttk/status').then((r) => r.data),

  startTTKIndexing: () => api.post('/admin/ttk/index').then((r) => r.data),

  loadTTKPdf: () => api.post('/admin/ttk/load').then((r) => r.data),
}
