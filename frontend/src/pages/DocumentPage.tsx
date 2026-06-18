import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { documentService } from '@/services/document.service'
import PDFViewer from '@/components/DocumentViewer/PDFViewer'
import AnnotationPanel from '@/components/DocumentViewer/AnnotationPanel'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import { ArrowLeft, BarChart2, Download, RefreshCw } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { analysisService } from '@/services/analysis.service'
import toast from 'react-hot-toast'

export default function DocumentPage() {
  const { id } = useParams<{ id: string }>()
  const docId = Number(id)
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: doc, isLoading } = useQuery({
    queryKey: ['document', docId],
    queryFn: () => documentService.get(docId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'uploaded' || status === 'processing' ? 3000 : false
    },
  })

  const { mutate: startAnalysis, isPending: analyzing } = useMutation({
    mutationFn: () => analysisService.start(docId),
    onSuccess: () => {
      toast.success('Analiz başlatıldı')
      qc.invalidateQueries({ queryKey: ['document', docId] })
      navigate(`/documents/${docId}/analysis`)
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Analiz başlatılamadı'),
  })

  const { mutate: retryExtraction, isPending: retrying } = useMutation({
    mutationFn: () => documentService.retryExtraction(docId),
    onSuccess: () => {
      toast.success('Metin çıkarma yeniden başlatıldı')
      qc.invalidateQueries({ queryKey: ['document', docId] })
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Yeniden deneme başlatılamadı'),
  })

  const handleDownload = async () => {
    try {
      await documentService.downloadWithAuth(docId, doc?.original_filename)
      toast.success('Dosya indiriliyor...')
    } catch {
      toast.error('Dosya indirilemedi')
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!doc) return <p className="text-red-500">Doküman bulunamadı</p>

  const IMAGE_TYPES = ['png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp', 'webp']
  const isPdf = doc.file_type === 'pdf'
  const isImage = IMAGE_TYPES.includes(doc.file_type || '')
  const fileUrl = doc.file_url || `/uploads/${doc.filename}`
  const isError = doc.status === 'error'
  const isReady = doc.status === 'text_extracted'

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      {/* Header */}
      <div className="flex items-center gap-4 mb-4">
        <button onClick={() => navigate('/')} className="p-2 hover:bg-gray-200 rounded-lg transition-colors">
          <ArrowLeft size={18} />
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="font-semibold text-gray-900 truncate">{doc.original_filename}</h1>
          <p className="text-xs text-gray-400">{doc.page_count ?? 0} sayfa · {doc.file_type?.toUpperCase()}
            {isError && <span className="ml-2 text-red-500">● Hata</span>}
            {doc.status === 'uploaded' && <span className="ml-2 text-yellow-500">● İşleniyor...</span>}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleDownload}
            className="btn-secondary flex items-center gap-1.5 text-sm"
          >
            <Download size={14} />
            İndir
          </button>
          {isError && (
            <button
              onClick={() => retryExtraction()}
              disabled={retrying}
              className="btn-secondary flex items-center gap-1.5 text-sm text-orange-600 border-orange-300 hover:bg-orange-50"
            >
              <RefreshCw size={14} className={retrying ? 'animate-spin' : ''} />
              {retrying ? 'Deneniyor...' : 'Yeniden Dene'}
            </button>
          )}
          {doc.has_analysis ? (
            <button
              onClick={() => navigate(`/documents/${docId}/analysis`)}
              className="btn-primary flex items-center gap-1.5 text-sm"
            >
              <BarChart2 size={14} />
              Analizi Gör
            </button>
          ) : (
            <button
              onClick={() => startAnalysis()}
              disabled={analyzing || !isReady}
              className="btn-primary flex items-center gap-1.5 text-sm"
              title={!isReady ? (isError ? 'Önce Yeniden Dene butonuna tıklayın' : 'Metin çıkarılıyor...') : ''}
            >
              <BarChart2 size={14} />
              {analyzing ? 'Başlatılıyor...' : 'Analiz Et'}
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex flex-1 gap-4 overflow-hidden">
        <div className="flex-1 card overflow-hidden">
          {isPdf ? (
            <PDFViewer fileUrl={fileUrl} />
          ) : isImage ? (
            <div className="p-4 h-full overflow-auto flex items-start justify-center bg-gray-50">
              <img
                src={fileUrl}
                alt={doc.original_filename}
                className="max-w-full rounded shadow-md"
                style={{ maxHeight: '100%', objectFit: 'contain' }}
              />
            </div>
          ) : (
            <div className="p-6 h-full overflow-y-auto">
              <p className="text-sm text-gray-500 mb-4">DOCX önizleme desteklenmiyor. Dosyayı indirerek görüntüleyebilirsiniz.</p>
              <button onClick={handleDownload} className="btn-primary inline-flex items-center gap-2">
                <Download size={14} />
                Dosyayı İndir
              </button>
            </div>
          )}
        </div>
        <div className="w-72 card overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200">
            <h2 className="font-semibold text-sm">Notlar & Annotationlar</h2>
          </div>
          <AnnotationPanel docId={docId} />
        </div>
      </div>
    </div>
  )
}
