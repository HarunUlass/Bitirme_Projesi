import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { documentService } from '@/services/document.service'
import { Plus, Trash2, StickyNote, Flag, Highlighter } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { tr } from 'date-fns/locale'
import toast from 'react-hot-toast'
import type { Annotation } from '@/types'

const TYPE_CONFIG = {
  note: { icon: StickyNote, label: 'Not', color: '#FFEB3B' },
  highlight: { icon: Highlighter, label: 'Vurgu', color: '#A7F3D0' },
  flag: { icon: Flag, label: 'Bayrak', color: '#FCA5A5' },
}

export default function AnnotationPanel({ docId }: { docId: number }) {
  const qc = useQueryClient()
  const [content, setContent] = useState('')
  const [type, setType] = useState<'note' | 'highlight' | 'flag'>('note')
  const [page, setPage] = useState(1)

  const { data: annotations = [] } = useQuery({
    queryKey: ['annotations', docId],
    queryFn: () => documentService.listAnnotations(docId),
  })

  const { mutate: create, isPending: creating } = useMutation({
    mutationFn: () =>
      documentService.createAnnotation(docId, {
        content,
        annotation_type: type,
        page_number: page,
        color: TYPE_CONFIG[type].color,
      }),
    onSuccess: () => {
      setContent('')
      qc.invalidateQueries({ queryKey: ['annotations', docId] })
      toast.success('Annotation eklendi')
    },
  })

  const { mutate: del } = useMutation({
    mutationFn: (annId: number) => documentService.deleteAnnotation(docId, annId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['annotations', docId] }),
  })

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-gray-200">
        <h3 className="font-semibold text-sm mb-3">Yeni Annotation</h3>
        <div className="flex gap-2 mb-3">
          {(Object.keys(TYPE_CONFIG) as Array<keyof typeof TYPE_CONFIG>).map((t) => {
            const cfg = TYPE_CONFIG[t]
            return (
              <button
                key={t}
                onClick={() => setType(t)}
                className={`flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-colors ${type === t ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
                  }`}
              >
                <cfg.icon size={12} />
                {cfg.label}
              </button>
            )
          })}
        </div>
        <div className="flex items-center gap-2 mb-2">
          <label className="text-xs text-gray-500">Sayfa:</label>
          <input
            type="number"
            min={1}
            value={page}
            onChange={(e) => setPage(Number(e.target.value))}
            className="w-16 text-xs border border-gray-300 rounded px-2 py-1"
          />
        </div>
        <textarea
          className="w-full text-sm border border-gray-300 rounded-lg p-2.5 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500"
          rows={3}
          placeholder="Not ekleyin..."
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
        <button
          onClick={() => create()}
          disabled={!content.trim() || creating}
          className="btn-primary w-full mt-2 text-sm py-1.5 flex items-center justify-center gap-1.5"
        >
          <Plus size={14} />
          Ekle
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {annotations.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-4">Henüz annotation yok</p>
        )}
        {annotations.map((ann) => {
          const cfg = TYPE_CONFIG[ann.annotation_type as keyof typeof TYPE_CONFIG] || TYPE_CONFIG.note
          return (
            <div
              key={ann.id}
              className="border border-gray-200 rounded-lg p-3"
              style={{ borderLeftColor: cfg.color, borderLeftWidth: 3 }}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-1.5 text-xs text-gray-500">
                  <cfg.icon size={11} />
                  {cfg.label} · Sayfa {ann.page_number}
                </div>
                <button onClick={() => del(ann.id)} className="text-gray-300 hover:text-red-500 transition-colors">
                  <Trash2 size={12} />
                </button>
              </div>
              <p className="text-sm text-gray-700 mt-1">{ann.content}</p>
              <p className="text-xs text-gray-400 mt-1">
                {formatDistanceToNow(new Date(ann.created_at), { addSuffix: true, locale: tr })}
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
