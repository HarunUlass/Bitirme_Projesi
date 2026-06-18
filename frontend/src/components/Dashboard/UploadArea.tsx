import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Image } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { documentService } from '@/services/document.service'
import toast from 'react-hot-toast'

const ACCEPT = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
  'image/png':  ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/tiff': ['.tiff', '.tif'],
  'image/bmp':  ['.bmp'],
  'image/webp': ['.webp'],
}

export default function UploadArea() {
  const qc = useQueryClient()
  const { mutate, isPending } = useMutation({
    mutationFn: documentService.upload,
    onSuccess: () => {
      toast.success('Doküman başarıyla yüklendi')
      qc.invalidateQueries({ queryKey: ['documents'] })
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Yükleme başarısız')
    },
  })

  const onDrop = useCallback(
    (files: File[]) => {
      files.forEach((f) => mutate(f))
    },
    [mutate]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT,
    maxSize: 50 * 1024 * 1024,
    disabled: isPending,
  })

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
        isDragActive
          ? 'border-primary-500 bg-primary-50'
          : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
      } ${isPending ? 'opacity-60 cursor-not-allowed' : ''}`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-3">
        {isPending ? (
          <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
        ) : (
          <div className="flex gap-2 text-gray-400">
            <Upload size={28} />
          </div>
        )}
        <div>
          <p className="font-medium text-gray-700">
            {isDragActive ? 'Dosyayı buraya bırakın' : 'Doküman veya Görsel Yükleyin'}
          </p>
          <p className="text-sm text-gray-400 mt-1">
            PDF, DOCX — Görsel: PNG, JPG, TIFF, BMP, WEBP
          </p>
          <p className="text-xs text-gray-300 mt-0.5">Sürükle &amp; bırak veya tıkla · max 50MB</p>
        </div>
        <div className="flex gap-3 mt-1">
          <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">PDF</span>
          <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">DOCX</span>
          <span className="text-xs bg-blue-50 text-blue-500 px-2 py-0.5 rounded">PNG</span>
          <span className="text-xs bg-blue-50 text-blue-500 px-2 py-0.5 rounded">JPG</span>
          <span className="text-xs bg-blue-50 text-blue-500 px-2 py-0.5 rounded">TIFF</span>
          <span className="text-xs bg-blue-50 text-blue-500 px-2 py-0.5 rounded">+daha fazla</span>
        </div>
      </div>
    </div>
  )
}
