import { AlertTriangle, Info, XCircle, Scale } from 'lucide-react'
import type { RiskFlag } from '@/types'
import { clsx } from 'clsx'

const RISK_CONFIG = {
  critical: {
    icon: XCircle,
    label: 'Kritik',
    className: 'bg-red-50 border-red-200 text-red-800',
    iconClass: 'text-red-500',
    badge: 'bg-red-100 text-red-700',
  },
  warning: {
    icon: AlertTriangle,
    label: 'Uyarı',
    className: 'bg-amber-50 border-amber-200 text-amber-800',
    iconClass: 'text-amber-500',
    badge: 'bg-amber-100 text-amber-700',
  },
  info: {
    icon: Info,
    label: 'Bilgi',
    className: 'bg-blue-50 border-blue-200 text-blue-800',
    iconClass: 'text-blue-500',
    badge: 'bg-blue-100 text-blue-700',
  },
}

export default function RiskPanel({ flags }: { flags: RiskFlag[] }) {
  if (!flags?.length) {
    return (
      <div className="text-center py-8 text-gray-400">
        <Info size={32} className="mx-auto mb-2" />
        <p className="text-sm">Risk tespit edilmedi</p>
      </div>
    )
  }

  const grouped = {
    critical: flags.filter((f) => f.level === 'critical'),
    warning: flags.filter((f) => f.level === 'warning'),
    info: flags.filter((f) => f.level === 'info'),
  }

  return (
    <div className="space-y-3">
      {/* Risk Summary */}
      <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg mb-2">
        <Scale size={16} className="text-primary-600 shrink-0" />
        <p className="text-xs text-gray-600">
          Riskler <span className="font-semibold">6102 sayılı TTK</span> ve <span className="font-semibold">6098 sayılı TBK</span> hükümlerine göre değerlendirilmiştir.
        </p>
      </div>

      {/* Risk Counts */}
      <div className="flex gap-2 mb-1">
        {grouped.critical.length > 0 && (
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-red-100 text-red-700 border border-red-200">
            {grouped.critical.length} Kritik
          </span>
        )}
        {grouped.warning.length > 0 && (
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-amber-100 text-amber-700 border border-amber-200">
            {grouped.warning.length} Uyarı
          </span>
        )}
        {grouped.info.length > 0 && (
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-blue-100 text-blue-700 border border-blue-200">
            {grouped.info.length} Bilgi
          </span>
        )}
      </div>

      {(['critical', 'warning', 'info'] as const).map((level) =>
        grouped[level].map((flag, i) => {
          const cfg = RISK_CONFIG[level]
          const Icon = cfg.icon
          return (
            <div
              key={`${level}-${i}`}
              className={clsx('border rounded-xl p-4 transition-all duration-200 hover:shadow-sm', cfg.className)}
            >
              <div className="flex items-start gap-3">
                <Icon size={18} className={clsx('shrink-0 mt-0.5', cfg.iconClass)} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={clsx('text-xs font-semibold px-2 py-0.5 rounded-full', cfg.badge)}>
                      {cfg.label}
                    </span>
                    <span className="font-semibold text-sm">{flag.title}</span>
                  </div>
                  <p className="text-sm mt-1.5 opacity-90 leading-relaxed">{flag.description}</p>
                  {flag.clause && (
                    <p className="text-xs mt-1.5 opacity-70 italic">📄 Madde: {flag.clause}</p>
                  )}
                  {flag.legal_reference && (
                    <div className="mt-2 flex items-center gap-1.5">
                      <Scale size={12} className="text-primary-600 shrink-0" />
                      <span className="text-xs font-medium text-primary-700 bg-primary-50 px-2 py-0.5 rounded-md border border-primary-200">
                        {flag.legal_reference}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}
