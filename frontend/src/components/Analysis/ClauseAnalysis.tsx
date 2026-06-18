import { ChevronDown, ChevronUp, Scale } from 'lucide-react'
import { useState } from 'react'
import type { Clause } from '@/types'
import { clsx } from 'clsx'

const RISK_BADGE = {
  low: 'bg-green-100 text-green-700 border-green-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  critical: 'bg-red-100 text-red-700 border-red-200',
}

const RISK_LABEL = { low: 'Düşük', medium: 'Orta', high: 'Yüksek', critical: 'Kritik' }

export default function ClauseAnalysis({ clauses }: { clauses: Clause[] }) {
  const [open, setOpen] = useState<number | null>(null)

  if (!clauses?.length) return <p className="text-sm text-gray-400 py-4">Madde analizi bulunamadı.</p>

  return (
    <div className="space-y-2">
      {clauses.map((clause, i) => (
        <div key={i} className="border border-gray-200 rounded-xl overflow-hidden hover:shadow-sm transition-all duration-200">
          <button
            onClick={() => setOpen(open === i ? null : i)}
            className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <span className="text-sm font-medium text-gray-800 truncate">{clause.title}</span>
              {clause.risk_level && (
                <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium shrink-0 border', RISK_BADGE[clause.risk_level])}>
                  {RISK_LABEL[clause.risk_level]}
                </span>
              )}
            </div>
            {open === i ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
          </button>

          {open === i && (
            <div className="px-4 pb-4 border-t border-gray-100">
              {clause.content && (
                <div className="mt-3">
                  <p className="text-xs font-semibold text-gray-500 mb-1">İçerik Özeti</p>
                  <p className="text-sm text-gray-700 leading-relaxed">{clause.content}</p>
                </div>
              )}
              {clause.analysis && (
                <div className="mt-3">
                  <p className="text-xs font-semibold text-gray-500 mb-1">Hukuki Analiz (TTK/TBK)</p>
                  <p className="text-sm text-gray-700 leading-relaxed">{clause.analysis}</p>
                </div>
              )}
              {clause.legal_reference && (
                <div className="mt-3 flex items-center gap-1.5">
                  <Scale size={12} className="text-primary-600 shrink-0" />
                  <span className="text-xs font-medium text-primary-700 bg-primary-50 px-2 py-0.5 rounded-md border border-primary-200">
                    {clause.legal_reference}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
