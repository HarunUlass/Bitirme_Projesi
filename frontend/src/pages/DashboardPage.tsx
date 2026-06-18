import { useQuery } from '@tanstack/react-query'
import { documentService } from '@/services/document.service'
import { useAuthStore } from '@/store/authStore'
import DocumentCard from '@/components/Dashboard/DocumentCard'
import UploadArea from '@/components/Dashboard/UploadArea'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import { FileText, Upload } from 'lucide-react'

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const { data, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentService.list(1, 50),
  })

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Hoş geldin, {user?.full_name} 👋
        </h1>
        <p className="text-gray-500 mt-1">Hukuki dokümanlarınızı yükleyin ve analiz edin</p>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="card p-4">
          <p className="text-xs text-gray-500 mb-1">Toplam Doküman</p>
          <p className="text-2xl font-bold text-gray-900">{data?.total ?? 0}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-gray-500 mb-1">Analiz Edilmiş</p>
          <p className="text-2xl font-bold text-primary-700">
            {data?.items.filter((d) => d.has_analysis).length ?? 0}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-gray-500 mb-1">Bekleyen</p>
          <p className="text-2xl font-bold text-amber-600">
            {data?.items.filter((d) => !d.has_analysis).length ?? 0}
          </p>
        </div>
      </div>

      <div className="card p-5 mb-6">
        <h2 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <Upload size={16} /> Doküman Yükle
        </h2>
        <UploadArea />
      </div>

      <div className="card p-5">
        <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <FileText size={16} /> Dokümanlarım
          <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full ml-auto">
            {data?.total ?? 0}
          </span>
        </h2>

        {isLoading && (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {!isLoading && !data?.items.length && (
          <div className="text-center py-12 text-gray-400">
            <FileText size={40} className="mx-auto mb-3 opacity-40" />
            <p>Henüz doküman yüklenmedi</p>
            <p className="text-sm mt-1">Yukarıdan PDF, DOCX veya görsel yükleyerek başlayın</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data?.items.map((doc) => <DocumentCard key={doc.id} doc={doc} />)}
        </div>
      </div>
    </div>
  )
}
