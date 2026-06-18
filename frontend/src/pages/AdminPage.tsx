import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/analysis.service'
import { useDropzone } from 'react-dropzone'
import { Trash2, Upload, FileText, Users, Shield, RefreshCw, CheckCircle, XCircle, Clock, Loader2, HardDrive, BookOpen, Play, Database } from 'lucide-react'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import toast from 'react-hot-toast'
import { formatDistanceToNow } from 'date-fns'
import { tr } from 'date-fns/locale'

function formatFileSize(bytes: number): string {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case 'indexed':
      return (
        <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-green-100 text-green-700 border border-green-200">
          <CheckCircle size={11} />
          İndekslendi
        </span>
      )
    case 'error':
      return (
        <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-red-100 text-red-700 border border-red-200">
          <XCircle size={11} />
          Hata
        </span>
      )
    case 'uploaded':
      return (
        <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200 animate-pulse">
          <Loader2 size={11} className="animate-spin" />
          İşleniyor
        </span>
      )
    case 'text_extracted':
      return (
        <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 border border-blue-200">
          <Clock size={11} />
          Metin Çıkarıldı
        </span>
      )
    default:
      return (
        <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
          {status}
        </span>
      )
  }
}

export default function AdminPage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<'contracts' | 'users' | 'ttk'>('contracts')

  const { data: contracts, isLoading: loadingContracts } = useQuery({
    queryKey: ['admin', 'contracts'],
    queryFn: () => adminService.listReferenceContracts(),
    refetchInterval: (q) => {
      const items = q.state.data?.items || []
      const hasProcessing = items.some((d: any) => d.status === 'uploaded' || d.status === 'text_extracted')
      return hasProcessing ? 4000 : false
    },
  })

  const { data: ttkStatus } = useQuery({
    queryKey: ['admin', 'ttk-status'],
    queryFn: () => adminService.getTTKStatus(),
    refetchInterval: (q) => (q.state.data?.is_running || q.state.data?.load_state?.is_running ? 2000 : 10000),
  })

  const { mutate: startIndexing, isPending: indexing } = useMutation({
    mutationFn: adminService.startTTKIndexing,
    onSuccess: () => {
      toast.success('TTK indeksleme başlatıldı')
      qc.invalidateQueries({ queryKey: ['admin', 'ttk-status'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'İndeksleme başlatılamadı'),
  })

  const { mutate: loadPdf, isPending: loadingPdf } = useMutation({
    mutationFn: adminService.loadTTKPdf,
    onSuccess: () => {
      toast.success('TTK PDF belleğe yükleme başlatıldı')
      qc.invalidateQueries({ queryKey: ['admin', 'ttk-status'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'PDF yükleme başlatılamadı'),
  })

  const { data: users, isLoading: loadingUsers } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => adminService.listUsers(),
    enabled: tab === 'users',
  })

  const { mutate: upload, isPending: uploading } = useMutation({
    mutationFn: adminService.uploadReferenceContract,
    onSuccess: () => {
      toast.success('Referans sözleşme eklendi ve indeksleniyor...')
      qc.invalidateQueries({ queryKey: ['admin', 'contracts'] })
    },
    onError: () => toast.error('Yükleme başarısız'),
  })

  const { mutate: retry, isPending: retrying } = useMutation({
    mutationFn: adminService.retryReferenceContract,
    onSuccess: () => {
      toast.success('Yeniden işleme başlatıldı')
      qc.invalidateQueries({ queryKey: ['admin', 'contracts'] })
    },
    onError: () => toast.error('Yeniden işleme başarısız'),
  })

  const { mutate: del } = useMutation({
    mutationFn: adminService.deleteReferenceContract,
    onSuccess: () => {
      toast.success('Silindi')
      qc.invalidateQueries({ queryKey: ['admin', 'contracts'] })
    },
  })

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (files) => files.forEach((f) => upload(f)),
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
    disabled: uploading,
  })

  const errorCount = contracts?.items?.filter((d: any) => d.status === 'error').length || 0
  const indexedCount = contracts?.items?.filter((d: any) => d.status === 'indexed').length || 0

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl shadow-lg shadow-primary-200">
          <Shield size={22} className="text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-sm text-gray-500">Referans sözleşme kütüphanesi ve kullanıcı yönetimi</p>
        </div>
      </div>

      <div className="flex gap-2 mb-6">
        {[
          { key: 'contracts', label: 'Referans Sözleşmeler', icon: FileText },
          { key: 'ttk', label: 'TTK Bilgi Tabanı', icon: BookOpen },
          { key: 'users', label: 'Kullanıcılar', icon: Users },
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key as typeof tab)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${tab === key ? 'bg-primary-600 text-white shadow-md shadow-primary-200' : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 hover:border-gray-400'
              }`}
          >
            <Icon size={15} />
            {label}
            {key === 'contracts' && errorCount > 0 && (
              <span className="ml-1 bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full font-bold">
                {errorCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {tab === 'contracts' && (
        <div className="space-y-4">
          {/* Stats Row */}
          <div className="grid grid-cols-3 gap-3">
            <div className="card p-4 bg-gradient-to-br from-white to-gray-50">
              <p className="text-xs text-gray-500 mb-1">Toplam</p>
              <p className="text-2xl font-bold text-gray-900">{contracts?.total ?? 0}</p>
            </div>
            <div className="card p-4 bg-gradient-to-br from-white to-green-50">
              <p className="text-xs text-gray-500 mb-1">İndekslenmiş</p>
              <p className="text-2xl font-bold text-green-700">{indexedCount}</p>
            </div>
            <div className="card p-4 bg-gradient-to-br from-white to-red-50">
              <p className="text-xs text-gray-500 mb-1">Hatalı</p>
              <p className="text-2xl font-bold text-red-600">{errorCount}</p>
            </div>
          </div>

          <div className="card p-5">
            <h2 className="font-semibold text-sm text-gray-800 mb-3 flex items-center gap-2">
              <Upload size={15} /> Referans Sözleşme Ekle
            </h2>
            <p className="text-xs text-gray-500 mb-3">
              Bu sözleşmeler RAG pipeline'a eklenerek kullanıcı dokümanlarıyla TTK kapsamında karşılaştırılır.
            </p>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 ${isDragActive ? 'border-primary-500 bg-primary-50 scale-[1.01]' : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
                } ${uploading ? 'opacity-60 pointer-events-none' : ''}`}
            >
              <input {...getInputProps()} />
              {uploading ? (
                <div className="flex flex-col items-center gap-2">
                  <LoadingSpinner />
                  <p className="text-sm text-gray-500">Yükleniyor ve indeksleniyor...</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <div className="p-3 bg-primary-100 rounded-full">
                    <Upload size={24} className="text-primary-600" />
                  </div>
                  <p className="text-sm font-medium text-gray-700">PDF veya DOCX sürükleyin</p>
                  <p className="text-xs text-gray-400">veya tıklayarak seçin</p>
                </div>
              )}
            </div>
          </div>

          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-sm text-gray-800">
                Referans Kütüphane ({contracts?.total ?? 0})
              </h2>
              {errorCount > 0 && (
                <span className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded-lg border border-red-200">
                  {errorCount} hatalı sözleşme
                </span>
              )}
            </div>
            {loadingContracts ? (
              <div className="flex justify-center py-8"><LoadingSpinner /></div>
            ) : !contracts?.items.length ? (
              <div className="text-center py-12 text-gray-400">
                <FileText size={40} className="mx-auto mb-3 opacity-40" />
                <p className="text-sm">Henüz referans sözleşme eklenmedi</p>
                <p className="text-xs mt-1">Yukarıdan PDF veya DOCX yükleyerek başlayın</p>
              </div>
            ) : (
              <div className="space-y-2">
                {contracts.items.map((doc: any) => (
                  <div
                    key={doc.id}
                    className={`flex items-center gap-3 px-4 py-3.5 border rounded-lg transition-all duration-200 hover:shadow-sm ${doc.status === 'error'
                        ? 'border-red-200 bg-red-50/50'
                        : doc.status === 'indexed'
                          ? 'border-green-200 bg-green-50/30'
                          : 'border-gray-200 bg-white'
                      }`}
                  >
                    <div className={`p-2 rounded-lg shrink-0 ${doc.status === 'error' ? 'bg-red-100' :
                        doc.status === 'indexed' ? 'bg-green-100' : 'bg-gray-100'
                      }`}>
                      <FileText size={16} className={`${doc.status === 'error' ? 'text-red-500' :
                          doc.status === 'indexed' ? 'text-green-600' : 'text-gray-400'
                        }`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate text-gray-800">{doc.original_filename}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-gray-400">
                          {formatDistanceToNow(new Date(doc.created_at), { addSuffix: true, locale: tr })}
                        </span>
                        <span className="text-gray-300">·</span>
                        <span className="text-xs text-gray-400 flex items-center gap-1">
                          <HardDrive size={10} />
                          {formatFileSize(doc.file_size)}
                        </span>
                        <span className="text-gray-300">·</span>
                        <StatusBadge status={doc.status} />
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      {doc.status === 'error' && (
                        <button
                          onClick={() => retry(doc.id)}
                          disabled={retrying}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded-lg transition-colors border border-amber-200 disabled:opacity-50"
                          title="Yeniden İşle"
                        >
                          <RefreshCw size={12} className={retrying ? 'animate-spin' : ''} />
                          Yeniden Dene
                        </button>
                      )}
                      <button
                        onClick={() => confirm('Silmek istediğinize emin misiniz?') && del(doc.id)}
                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        title="Sil"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'ttk' && (
        <div className="space-y-4">
          {/* Durum Kartları */}
          <div className="grid grid-cols-4 gap-3">
            <div className="card p-4 bg-gradient-to-br from-white to-purple-50">
              <p className="text-xs text-gray-500 mb-1">PDF Sayfa Sayısı</p>
              <p className="text-2xl font-bold text-purple-700">{ttkStatus?.page_count ?? '—'}</p>
            </div>
            <div className="card p-4 bg-gradient-to-br from-white to-blue-50">
              <p className="text-xs text-gray-500 mb-1">Bulunan Madde</p>
              <p className="text-2xl font-bold text-blue-700">{ttkStatus?.article_count ?? '—'}</p>
            </div>
            <div className="card p-4 bg-gradient-to-br from-white to-green-50">
              <p className="text-xs text-gray-500 mb-1">İndekslenmiş Madde</p>
              <p className="text-2xl font-bold text-green-700">{ttkStatus?.db_indexed_count ?? '—'}</p>
            </div>
            <div className="card p-4 bg-gradient-to-br from-white to-gray-50">
              <p className="text-xs text-gray-500 mb-1">PDF Durumu</p>
              <p className="text-sm font-semibold mt-1">
                {ttkStatus?.pdf_loaded
                  ? <span className="text-green-600 flex items-center gap-1"><CheckCircle size={14} /> Yüklü</span>
                  : <span className="text-red-500 flex items-center gap-1"><XCircle size={14} /> Yüklenmemiş</span>
                }
              </p>
            </div>
          </div>

          {/* Adım 1: PDF'i Belleğe Yükle */}
          <div className="card p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center justify-center w-7 h-7 rounded-full bg-blue-100 text-blue-700 text-sm font-bold shrink-0">1</div>
              <div>
                <h2 className="font-semibold text-sm text-gray-800 flex items-center gap-2">
                  <BookOpen size={15} /> PDF'i Belleğe Yükle
                </h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  TTK PDF'ini okur, tüm sayfaları tarar ve maddelere ayırır. İndeksleme öncesi gereklidir.
                </p>
              </div>
            </div>

            {/* Yükleniyor */}
            {ttkStatus?.load_state?.is_running && (
              <div className="mb-4 flex items-center gap-2 text-sm text-blue-700 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
                <Loader2 size={15} className="animate-spin" />
                PDF okunuyor ve maddelere ayrılıyor...
              </div>
            )}

            {/* Tamamlandı */}
            {ttkStatus?.load_state?.completed && !ttkStatus?.load_state?.is_running && ttkStatus?.pdf_loaded && (
              <div className="mb-4 flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                <CheckCircle size={15} />
                PDF belleğe yüklendi — {ttkStatus.page_count} sayfadan {ttkStatus.article_count} madde bulundu.
              </div>
            )}

            {/* Hata */}
            {ttkStatus?.load_state?.error && (
              <div className="mb-4 flex items-center gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                <XCircle size={15} />
                {ttkStatus.load_state.error}
              </div>
            )}

            <button
              onClick={() => loadPdf()}
              disabled={loadingPdf || ttkStatus?.load_state?.is_running}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm shadow-blue-200"
            >
              {ttkStatus?.load_state?.is_running
                ? <><Loader2 size={15} className="animate-spin" /> Yükleniyor...</>
                : <><BookOpen size={15} /> {ttkStatus?.pdf_loaded ? 'Yeniden Yükle' : 'PDF\'i Belleğe Yükle'}</>
              }
            </button>
            {ttkStatus?.pdf_loaded && !ttkStatus?.load_state?.is_running && (
              <p className="text-xs text-gray-400 mt-2">
                Tekrar basılırsa PDF yeniden okunur ve maddeler güncellenir.
              </p>
            )}
          </div>

          {/* Adım 2: İndeksleme */}
          <div className={`card p-5 transition-opacity ${!ttkStatus?.pdf_loaded ? 'opacity-50' : ''}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className={`flex items-center justify-center w-7 h-7 rounded-full text-sm font-bold shrink-0 ${
                ttkStatus?.pdf_loaded ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-400'
              }`}>2</div>
              <div>
                <h2 className="font-semibold text-sm text-gray-800 flex items-center gap-2">
                  <Database size={15} /> TTK Vektör İndeksleme
                </h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  Belleğe yüklenen {ttkStatus?.article_count ?? '...'} maddeyi ChromaDB'ye indeksler.
                  Analiz sırasında ilgili maddeler otomatik seçilir.
                </p>
              </div>
            </div>

            {/* İlerleme çubuğu */}
            {ttkStatus?.is_running && ttkStatus.total > 0 && (
              <div className="mb-4">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>İndeksleniyor...</span>
                  <span>{ttkStatus.indexed} / {ttkStatus.total}
                    {ttkStatus.skipped > 0 && <span className="text-amber-500 ml-1">({ttkStatus.skipped} atlandı)</span>}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${Math.round((ttkStatus.indexed / ttkStatus.total) * 100)}%` }}
                  />
                </div>
              </div>
            )}

            {/* Tamamlandı */}
            {ttkStatus?.completed && !ttkStatus.is_running && (
              <div className="mb-4 flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                <CheckCircle size={15} />
                İndeksleme tamamlandı — {ttkStatus.db_indexed_count} madde hazır.
              </div>
            )}

            {/* Hata */}
            {ttkStatus?.error && (
              <div className="mb-4 flex items-center gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                <XCircle size={15} />
                {ttkStatus.error}
              </div>
            )}

            <button
              onClick={() => startIndexing()}
              disabled={indexing || ttkStatus?.is_running || !ttkStatus?.pdf_loaded}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm shadow-primary-200"
            >
              {ttkStatus?.is_running
                ? <><Loader2 size={15} className="animate-spin" /> İndeksleniyor...</>
                : <><Play size={15} /> İndekslemeyi Başlat</>
              }
            </button>
            {!ttkStatus?.pdf_loaded && (
              <p className="text-xs text-amber-500 mt-2 flex items-center gap-1">
                <Clock size={11} /> Önce Adım 1'deki butona basarak PDF'i belleğe yükleyin.
              </p>
            )}
            {ttkStatus?.db_indexed_count > 0 && !ttkStatus.is_running && ttkStatus?.pdf_loaded && (
              <p className="text-xs text-gray-400 mt-2">
                Butona tekrar basılırsa kaldığı yerden devam eder.
              </p>
            )}
          </div>
        </div>
      )}

      {tab === 'users' && (
        <div className="card p-5">
          <h2 className="font-semibold text-sm text-gray-800 mb-4">Kullanıcılar</h2>
          {loadingUsers ? (
            <div className="flex justify-center py-8"><LoadingSpinner /></div>
          ) : (
            <div className="space-y-2">
              {users?.map((u: any) => (
                <div key={u.id} className="flex items-center gap-3 px-3 py-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0 shadow-sm">
                    {u.full_name?.[0]?.toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{u.full_name}</p>
                    <p className="text-xs text-gray-400">{u.email}</p>
                  </div>
                  <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${u.role === 'admin' ? 'bg-primary-100 text-primary-700 border border-primary-200' : 'bg-gray-100 text-gray-600 border border-gray-200'
                    }`}>
                    {u.role}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
