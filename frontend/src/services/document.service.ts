import api from './api'
import type { Document, DocumentListResponse, Annotation } from '@/types'

export const documentService = {
  list: (page = 1, size = 20) =>
    api.get<DocumentListResponse>('/documents', { params: { page, size } }).then((r) => r.data),

  get: (id: number) => api.get<Document>(`/documents/${id}`).then((r) => r.data),

  upload: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post<Document>('/documents/upload', fd).then((r) => r.data)
  },

  retryExtraction: (id: number) =>
    api.post<Document>(`/documents/${id}/retry-extraction`).then((r) => r.data),

  delete: (id: number) => api.delete(`/documents/${id}`),

  download: (id: number) => `/api/v1/documents/${id}/download`,

  downloadWithAuth: async (id: number, filename?: string) => {
    const response = await api.get(`/documents/${id}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([response.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = filename || `document_${id}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },

  listAnnotations: (docId: number) =>
    api.get<Annotation[]>(`/documents/${docId}/annotations`).then((r) => r.data),

  createAnnotation: (docId: number, payload: Partial<Annotation>) =>
    api.post<Annotation>(`/documents/${docId}/annotations`, payload).then((r) => r.data),

  deleteAnnotation: (docId: number, annId: number) =>
    api.delete(`/documents/${docId}/annotations/${annId}`),
}
