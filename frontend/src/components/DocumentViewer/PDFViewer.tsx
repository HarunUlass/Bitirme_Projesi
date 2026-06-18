import { useState } from 'react'
import { pdfjs, Document, Page } from 'react-pdf'
import { ZoomIn, ZoomOut } from 'lucide-react'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import 'react-pdf/dist/Page/TextLayer.css'
import 'react-pdf/dist/Page/AnnotationLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

interface Props {
  fileUrl: string
  onPageChange?: (page: number) => void
}

export default function PDFViewer({ fileUrl, onPageChange }: Props) {
  const [numPages, setNumPages] = useState(0)
  const [scale, setScale] = useState(1.0)

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b border-gray-200">
        <span className="text-sm text-gray-600">{numPages} sayfa</span>
        <div className="flex items-center gap-2">
          <button onClick={() => setScale((s) => Math.max(s - 0.2, 0.5))} className="p-1 rounded hover:bg-gray-200">
            <ZoomOut size={16} />
          </button>
          <span className="text-xs text-gray-500">{Math.round(scale * 100)}%</span>
          <button onClick={() => setScale((s) => Math.min(s + 0.2, 2.5))} className="p-1 rounded hover:bg-gray-200">
            <ZoomIn size={16} />
          </button>
        </div>
      </div>

      {/* PDF - all pages scrollable */}
      <div className="flex-1 overflow-auto flex flex-col items-center bg-gray-200 p-4 gap-4">
        <Document
          file={fileUrl}
          onLoadSuccess={({ numPages: n }) => {
            setNumPages(n)
            onPageChange?.(1)
          }}
          loading={<div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>}
          error={<p className="text-red-500 text-sm py-8 text-center">PDF yüklenemedi</p>}
        >
          {Array.from({ length: numPages }, (_, i) => (
            <Page
              key={i + 1}
              pageNumber={i + 1}
              scale={scale}
              renderTextLayer
              renderAnnotationLayer={false}
              className="shadow-lg"
            />
          ))}
        </Document>
      </div>
    </div>
  )
}
