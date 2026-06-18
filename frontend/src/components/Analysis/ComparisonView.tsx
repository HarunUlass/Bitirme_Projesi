import { FileText, TrendingUp, ChevronDown, ChevronUp, Eye, X, BookOpen, Scale, Loader2, Download } from 'lucide-react'
import type { SimilarContract } from '@/types'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analysisService } from '@/services/analysis.service'
import PDFViewer from '@/components/DocumentViewer/PDFViewer'
import toast from 'react-hot-toast'

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color =
    pct >= 70 ? 'text-green-700 bg-green-50 border-green-200' :
    pct >= 40 ? 'text-yellow-700 bg-yellow-50 border-yellow-200' :
                'text-gray-600 bg-gray-50 border-gray-200'
  const bar =
    pct >= 70 ? 'bg-green-500' :
    pct >= 40 ? 'bg-yellow-400' :
                'bg-gray-300'
  return { pct, color, bar }
}

/* ─────── Detail Modal with PDF Viewer ─────── */
function ContractDetailModal({ docId, filename, onClose }: { docId: string; filename: string; onClose: () => void }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['reference-contract', docId],
    queryFn: () => analysisService.getReferenceContractDetail(docId),
  })
  const [tab, setTab] = useState<'viewer' | 'text'>('viewer')

  const handleDownload = async () => {
    try {
      await analysisService.downloadReferenceContract(docId, data?.original_filename || filename)
      toast.success('Dosya indiriliyor...')
    } catch {
      toast.error('İndirme başarısız')
    }
  }

  const isPdf = data?.file_type === 'pdf'
  const IMAGE_TYPES = ['png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp', 'webp']
  const isImage = IMAGE_TYPES.includes(data?.file_type || '')

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-3.5 border-b border-gray-200 bg-gradient-to-r from-primary-50 to-blue-50 shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 bg-primary-100 rounded-lg shrink-0">
              <BookOpen size={18} className="text-primary-700" />
            </div>
            <div className="min-w-0">
              <h2 className="font-bold text-gray-900 truncate text-sm">{data?.original_filename || filename}</h2>
              <p className="text-xs text-gray-500">Referans Sözleşme</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {data && (
              <>
                {/* Tabs */}
                <div className="flex bg-gray-100 rounded-lg p-0.5 mr-2">
                  <button
                    onClick={() => setTab('viewer')}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                      tab === 'viewer' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Görüntüle
                  </button>
                  <button
                    onClick={() => setTab('text')}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                      tab === 'text' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Metin
                  </button>
                </div>
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-primary-700 bg-primary-100 hover:bg-primary-200 rounded-lg transition-colors border border-primary-200"
                >
                  <Download size={13} />
                  İndir
                </button>
              </>
            )}
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Meta Bar */}
        {data && (
          <div className="flex items-center gap-4 px-6 py-2 bg-gray-50 border-b border-gray-200 text-xs text-gray-500 shrink-0">
            <span>{data.file_type?.toUpperCase()}</span>
            <span>·</span>
            <span>{data.page_count ?? '—'} sayfa</span>
            <span>·</span>
            <span>{data.file_size ? `${(data.file_size / 1024 / 1024).toFixed(1)} MB` : '—'}</span>
            <span>·</span>
            <span className={data.status === 'indexed' ? 'text-green-600 font-medium' : ''}>{data.status === 'indexed' ? '✓ İndekslendi' : data.status}</span>
          </div>
        )}

        {/* Body */}
        <div className="flex-1 overflow-hidden">
          {isLoading && (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <Loader2 size={32} className="animate-spin mb-3" />
              <p className="text-sm">Sözleşme yükleniyor...</p>
            </div>
          )}

          {error && (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <FileText size={40} className="mb-3 opacity-40" />
              <p className="font-medium text-gray-600">Bu sözleşme artık mevcut değil</p>
              <p className="text-sm mt-1 text-gray-400">Referans sözleşme silinmiş olabilir. Analizi yeniden çalıştırdığınızda güncel sonuçlar gösterilecektir.</p>
            </div>
          )}

          {data && tab === 'viewer' && (
            <div className="h-full">
              {isPdf && data.file_url ? (
                <PDFViewer fileUrl={data.file_url} />
              ) : isImage && data.file_url ? (
                <div className="p-4 h-full overflow-auto flex items-start justify-center bg-gray-50">
                  <img
                    src={data.file_url}
                    alt={data.original_filename}
                    className="max-w-full rounded shadow-md"
                    style={{ maxHeight: '100%', objectFit: 'contain' }}
                  />
                </div>
              ) : data.extracted_text ? (
                <div className="h-full overflow-y-auto p-6">
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                    {data.extracted_text}
                  </pre>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                  <FileText size={40} className="mb-3 opacity-40" />
                  <p className="text-sm">Önizleme mevcut değil</p>
                  <button onClick={handleDownload} className="mt-3 btn-primary text-sm flex items-center gap-1.5">
                    <Download size={14} />
                    Dosyayı İndir
                  </button>
                </div>
              )}
            </div>
          )}

          {data && tab === 'text' && (
            <div className="h-full overflow-y-auto p-6">
              {data.extracted_text ? (
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                  {data.extracted_text}
                </pre>
              ) : (
                <div className="text-center py-12 text-gray-400">
                  <FileText size={32} className="mx-auto mb-2 opacity-40" />
                  <p className="text-sm">Sözleşme metni henüz çıkarılmamış</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ─────── Contract Card ─────── */
function ContractCard({ c, index }: { c: SimilarContract; index: number }) {
  const [open, setOpen] = useState(false)
  const [showDetail, setShowDetail] = useState(false)
  const { pct, color, bar } = ScoreBadge({ score: c.score })

  return (
    <>
      <div className="border border-gray-200 rounded-xl overflow-hidden hover:shadow-md transition-all duration-200">
        {/* Header row */}
        <div className="flex items-center gap-3 p-4">
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-primary-100 to-primary-200 text-xs font-bold text-primary-700 shrink-0">
            {index + 1}
          </div>
          <FileText size={16} className="text-gray-400 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">{c.filename}</p>
            {c.summary && (
              <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{c.summary}</p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className={`text-sm font-bold px-2.5 py-1 rounded-lg border ${color}`}>
              %{pct}
            </span>
            <button
              onClick={() => setShowDetail(true)}
              className="p-1.5 text-primary-500 hover:text-primary-700 hover:bg-primary-50 rounded-lg transition-colors"
              title="Sözleşmeyi görüntüle ve indir"
            >
              <Eye size={15} />
            </button>
            {c.comparison && (
              <button
                onClick={() => setOpen(!open)}
                className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                title="Karşılaştırmayı göster"
              >
                {open ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
              </button>
            )}
          </div>
        </div>

        {/* Similarity bar */}
        <div className="h-1.5 bg-gray-100">
          <div
            className={`h-full ${bar} transition-all duration-500 ease-out rounded-full`}
            style={{ width: `${pct}%` }}
          />
        </div>

        {/* AI comparison (collapsible) */}
        {c.comparison && open && (
          <div className="px-4 py-3.5 bg-gradient-to-br from-blue-50 to-indigo-50 border-t border-blue-100">
            <p className="text-xs font-semibold text-blue-700 mb-2 flex items-center gap-1.5">
              <Scale size={13} />
              AI Karşılaştırma Analizi (TTK/TBK)
            </p>
            <p className="text-xs text-blue-900 leading-relaxed whitespace-pre-line">{c.comparison}</p>
          </div>
        )}
      </div>

      {showDetail && (
        <ContractDetailModal
          docId={c.doc_id}
          filename={c.filename}
          onClose={() => setShowDetail(false)}
        />
      )}
    </>
  )
}

export default function ComparisonView({ contracts }: { contracts: SimilarContract[] }) {
  if (!contracts?.length) {
    return (
      <div className="text-center py-8 text-gray-400">
        <TrendingUp size={32} className="mx-auto mb-2 opacity-40" />
        <p className="text-sm font-medium">Benzer sözleşme bulunamadı</p>
        <p className="text-xs mt-1 text-gray-300">
          Admin panelinden referans sözleşme eklenmelidir
        </p>
      </div>
    )
  }

  const withComparison = contracts.filter((c) => c.comparison).length

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-gray-500">
          {contracts.length} benzer sözleşme bulundu
          {withComparison > 0 && ` · ${withComparison} TTK/TBK karşılaştırması mevcut`}
        </p>
      </div>
      {contracts.map((c, i) => (
        <ContractCard key={i} c={c} index={i} />
      ))}
    </div>
  )
}
