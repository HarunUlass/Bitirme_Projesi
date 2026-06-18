import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { analysisService } from '@/services/analysis.service'
import SummaryPanel from '@/components/Analysis/SummaryPanel'
import RiskPanel from '@/components/Analysis/RiskPanel'
import ClauseAnalysis from '@/components/Analysis/ClauseAnalysis'
import ComparisonView from '@/components/Analysis/ComparisonView'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import { ArrowLeft, Download, RefreshCw, FileText, AlertTriangle, List, GitCompare } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'

type Tab = 'summary' | 'risks' | 'clauses' | 'comparison'

const TABS: { key: Tab; label: string; icon: React.ComponentType<{ size?: number }> }[] = [
  { key: 'summary', label: 'Özet', icon: FileText },
  { key: 'risks', label: 'Riskler', icon: AlertTriangle },
  { key: 'clauses', label: 'Maddeler', icon: List },
  { key: 'comparison', label: 'Karşılaştırma', icon: GitCompare },
]

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>()
  const docId = Number(id)
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('summary')

  const { data: analysis, isLoading } = useQuery({
    queryKey: ['analysis', docId],
    queryFn: () => analysisService.get(docId),
    refetchInterval: (q) => q.state.data?.status === 'running' || q.state.data?.status === 'pending' ? 3000 : false,
  })

  const { mutate: reanalyze, isPending: reanalyzing } = useMutation({
    mutationFn: (force: boolean) => analysisService.start(docId, force),
    onSuccess: () => {
      toast.success('Analiz yeniden başlatıldı')
      qc.invalidateQueries({ queryKey: ['analysis', docId] })
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Analiz başlatılamadı'),
  })

  const downloadReport = async () => {
    try {
      await analysisService.downloadReport(docId)
      toast.success('Rapor indiriliyor...')
    } catch {
      toast.error('Rapor indirilemedi')
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!analysis) return <p className="text-red-500">Analiz bulunamadı</p>

  const isRunning = analysis.status === 'running' || analysis.status === 'pending'

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate(`/documents/${docId}`)} className="p-2 hover:bg-gray-200 rounded-lg">
          <ArrowLeft size={18} />
        </button>
        <h1 className="font-bold text-xl text-gray-900 flex-1">Analiz Sonuçları</h1>
        <button
          onClick={() => reanalyze(true)}
          disabled={reanalyzing || analysis?.status === 'running' || analysis?.status === 'pending'}
          className="p-2 hover:bg-gray-200 rounded-lg disabled:opacity-40 transition-colors"
          title="Yeniden Analiz Et"
        >
          <RefreshCw size={16} className={reanalyzing ? 'animate-spin' : ''} />
        </button>
        {analysis.status === 'completed' && (
          <button onClick={downloadReport} className="btn-primary flex items-center gap-1.5 text-sm">
            <Download size={14} />
            PDF Rapor İndir
          </button>
        )}
      </div>

      {isRunning && (
        <div className="card p-6 text-center mb-6">
          <LoadingSpinner size="lg" />
          <p className="mt-3 text-gray-600 font-medium">Analiz yapılıyor...</p>
          <p className="text-sm text-gray-400 mt-1">Gemini AI dokümanı inceliyor, lütfen bekleyin</p>
        </div>
      )}

      {analysis.status === 'error' && (
        <div className="card p-6 text-center border-red-200 bg-red-50 mb-6">
          <p className="text-red-600 font-medium">Analiz Başarısız</p>
          <p className="text-sm text-red-400 mt-1">{analysis.error_message}</p>
          <button
            onClick={() => reanalyze(false)}
            disabled={reanalyzing}
            className="mt-4 btn-primary flex items-center gap-1.5 text-sm mx-auto"
          >
            <RefreshCw size={14} className={reanalyzing ? 'animate-spin' : ''} />
            {reanalyzing ? 'Başlatılıyor...' : 'Yeniden Analiz Yap'}
          </button>
        </div>
      )}

      {analysis.status === 'completed' && (
        <>
          {/* Tab Bar */}
          <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-6">
            {TABS.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-sm font-medium rounded-lg transition-colors ${tab === key ? 'bg-white text-primary-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                  }`}
              >
                <Icon size={14} />
                {label}
                {key === 'risks' && analysis.risk_flags?.length ? (
                  <span className="ml-1 bg-red-100 text-red-600 text-xs px-1.5 rounded-full">
                    {analysis.risk_flags.length}
                  </span>
                ) : null}
              </button>
            ))}
          </div>

          <div className="card p-6">
            {tab === 'summary' && <SummaryPanel analysis={analysis} />}
            {tab === 'risks' && <RiskPanel flags={analysis.risk_flags || []} />}
            {tab === 'clauses' && <ClauseAnalysis clauses={analysis.clauses || []} />}
            {tab === 'comparison' && <ComparisonView contracts={analysis.similar_contracts || []} />}
          </div>
        </>
      )}
    </div>
  )
}
