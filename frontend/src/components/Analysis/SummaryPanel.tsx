import type { Analysis } from '@/types'
import { Users, Calendar, FileText, Target, Scale, ShieldCheck, BarChart3 } from 'lucide-react'

const RISK_STYLES: Record<string, string> = {
  low: 'bg-green-100 text-green-700 border-green-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  critical: 'bg-red-100 text-red-700 border-red-200',
}

const RISK_LABELS: Record<string, string> = { low: 'Düşük Risk', medium: 'Orta Risk', high: 'Yüksek Risk', critical: 'Kritik Risk' }

const SCORE_COLOR = (score: number) => {
  if (score >= 80) return 'text-green-700'
  if (score >= 60) return 'text-yellow-700'
  if (score >= 40) return 'text-orange-600'
  return 'text-red-600'
}

export default function SummaryPanel({ analysis }: { analysis: Analysis }) {
  const riskLevel = analysis.overall_risk_level || 'low'
  const score = analysis.compliance_score

  return (
    <div className="space-y-6">
      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <FileText size={14} className="text-gray-500" />
            <p className="text-xs text-gray-500 font-medium">Doküman Türü</p>
          </div>
          <p className="font-semibold text-sm text-gray-800">{analysis.document_type || '—'}</p>
        </div>
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <ShieldCheck size={14} className="text-gray-500" />
            <p className="text-xs text-gray-500 font-medium">Risk Seviyesi</p>
          </div>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${RISK_STYLES[riskLevel] || RISK_STYLES.low}`}>
            {RISK_LABELS[riskLevel] || riskLevel}
          </span>
        </div>
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 size={14} className="text-gray-500" />
            <p className="text-xs text-gray-500 font-medium">TTK/TBK Uyumluluk</p>
          </div>
          <p className={`font-bold text-lg ${score != null ? SCORE_COLOR(score) : 'text-gray-400'}`}>
            {score?.toFixed(0) ?? '—'}<span className="text-sm font-normal text-gray-400">/100</span>
          </p>
        </div>
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <Scale size={14} className="text-gray-500" />
            <p className="text-xs text-gray-500 font-medium">Risk Sayısı</p>
          </div>
          <p className="font-bold text-lg text-gray-800">{analysis.risk_flags?.length ?? 0}</p>
        </div>
      </div>

      {/* TTK/TBK Notice */}
      <div className="flex items-center gap-2 p-3 bg-primary-50 rounded-xl border border-primary-200">
        <Scale size={15} className="text-primary-600 shrink-0" />
        <p className="text-xs text-primary-700">
          Bu analiz <span className="font-semibold">6102 sayılı Türk Ticaret Kanunu (TTK)</span> ve <span className="font-semibold">6098 sayılı Türk Borçlar Kanunu (TBK)</span> hükümlerine göre yapılmıştır.
        </p>
      </div>

      {/* Summary */}
      {analysis.summary && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <FileText size={15} /> Özet
          </h3>
          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">{analysis.summary}</p>
        </div>
      )}

      {/* Parties */}
      {analysis.parties?.length ? (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <Users size={15} /> Taraflar
          </h3>
          <div className="space-y-2">
            {analysis.parties.map((p, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-lg font-medium min-w-fit border border-primary-200">
                  {p.role}
                </span>
                <span className="text-gray-700">{p.name}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Key Dates */}
      {analysis.key_dates?.length ? (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <Calendar size={15} /> Önemli Tarihler
          </h3>
          <div className="space-y-2">
            {analysis.key_dates.map((d, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="text-gray-500 text-xs min-w-fit">{d.label}:</span>
                <span className="font-medium text-gray-800">{d.date}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Recommendations */}
      {analysis.recommendations?.length ? (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <Target size={15} /> Öneriler
          </h3>
          <ul className="space-y-2">
            {analysis.recommendations.map((r, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-600 bg-gray-50 rounded-lg p-3 border border-gray-100">
                <span className="text-primary-600 font-bold shrink-0">{i + 1}.</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  )
}
