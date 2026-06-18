import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { analysisService } from '@/services/analysis.service'
import { documentService } from '@/services/document.service'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import { ArrowLeft, Download, FileText } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ReportPage() {
  const { id } = useParams<{ id: string }>()
  const docId = Number(id)
  const navigate = useNavigate()

  const { data: doc } = useQuery({
    queryKey: ['document', docId],
    queryFn: () => documentService.get(docId),
  })
  const { data: analysis, isLoading } = useQuery({
    queryKey: ['analysis', docId],
    queryFn: () => analysisService.get(docId),
  })

  const download = async () => {
    try {
      await analysisService.downloadReport(docId)
      toast.success('Rapor indiriliyor...')
    } catch {
      toast.error('Rapor indirilemedi')
    }
  }

  if (isLoading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate(`/documents/${docId}/analysis`)} className="p-2 hover:bg-gray-200 rounded-lg">
          <ArrowLeft size={18} />
        </button>
        <h1 className="font-bold text-xl text-gray-900 flex-1">Rapor</h1>
      </div>

      <div className="card p-8 text-center">
        <div className="w-16 h-16 bg-primary-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <FileText size={32} className="text-primary-600" />
        </div>
        <h2 className="text-lg font-semibold text-gray-900 mb-2">PDF Rapor Hazır</h2>
        <p className="text-sm text-gray-500 mb-1">{doc?.original_filename}</p>
        {analysis?.status !== 'completed' ? (
          <p className="text-sm text-amber-600 mt-4">Analiz henüz tamamlanmadı</p>
        ) : (
          <>
            <p className="text-sm text-gray-400 mb-6">
              Analiz raporu PDF formatında indirilebilir
            </p>
            <button onClick={download} className="btn-primary inline-flex items-center gap-2">
              <Download size={16} />
              PDF Raporu İndir
            </button>
          </>
        )}
      </div>
    </div>
  )
}
