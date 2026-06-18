import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Trash2, BarChart2, Clock, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { tr } from 'date-fns/locale'
import { documentService } from '@/services/document.service'
import toast from 'react-hot-toast'
import type { Document } from '@/types'

const STATUS_CONFIG = {
  uploaded: { label: 'Yüklendi', icon: Clock, color: 'text-gray-500 bg-gray-100' },
  text_extracted: { label: 'Hazır', icon: CheckCircle, color: 'text-green-600 bg-green-50' },
  indexed: { label: 'İndekslendi', icon: CheckCircle, color: 'text-green-600 bg-green-50' },
  error: { label: 'Hata', icon: AlertCircle, color: 'text-red-600 bg-red-50' },
  processing: { label: 'İşleniyor', icon: Loader, color: 'text-blue-600 bg-blue-50' },
}

export default function DocumentCard({ doc }: { doc: Document }) {
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { mutate: del, isPending: deleting } = useMutation({
    mutationFn: () => documentService.delete(doc.id),
    onSuccess: () => {
      toast.success('Doküman silindi')
      qc.invalidateQueries({ queryKey: ['documents'] })
    },
    onError: () => toast.error('Silme başarısız'),
  })

  const cfg = STATUS_CONFIG[doc.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.uploaded
  const Icon = cfg.icon

  const fileSizeLabel =
    doc.file_size > 1024 * 1024
      ? `${(doc.file_size / 1024 / 1024).toFixed(1)} MB`
      : `${(doc.file_size / 1024).toFixed(0)} KB`

  return (
    <div className="card p-4 flex flex-col gap-3 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="p-2 bg-primary-50 rounded-lg shrink-0">
            <FileText size={20} className="text-primary-600" />
          </div>
          <div className="min-w-0">
            <p className="font-medium text-sm truncate" title={doc.original_filename}>
              {doc.original_filename}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              {fileSizeLabel} · {doc.page_count} sayfa · {doc.file_type?.toUpperCase()}
            </p>
          </div>
        </div>
        <span className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full font-medium ${cfg.color}`}>
          <Icon size={11} />
          {cfg.label}
        </span>
      </div>

      <p className="text-xs text-gray-400">
        {formatDistanceToNow(new Date(doc.created_at), { addSuffix: true, locale: tr })}
      </p>

      <div className="flex gap-2">
        <button
          onClick={() => navigate(`/documents/${doc.id}`)}
          className="flex-1 flex items-center justify-center gap-1.5 text-xs font-medium py-1.5 px-3 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
        >
          <FileText size={13} />
          Görüntüle
        </button>
        {doc.has_analysis ? (
          <button
            onClick={() => navigate(`/documents/${doc.id}/analysis`)}
            className="flex-1 flex items-center justify-center gap-1.5 text-xs font-medium py-1.5 px-3 rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors"
          >
            <BarChart2 size={13} />
            Analiz
          </button>
        ) : (
          <button
            onClick={() => navigate(`/documents/${doc.id}`)}
            className="flex-1 flex items-center justify-center gap-1.5 text-xs font-medium py-1.5 px-3 rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100 transition-colors"
          >
            <BarChart2 size={13} />
            Analiz Et
          </button>
        )}
        <button
          onClick={() => {
            if (confirm('Dokümanı silmek istediğinize emin misiniz?')) del()
          }}
          disabled={deleting}
          className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
        >
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  )
}
