import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import {
  LayoutDashboard, FileText, Shield, LogOut, ChevronRight, Settings
} from 'lucide-react'
import { clsx } from 'clsx'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
]

const adminItems = [
  { to: '/admin', label: 'Admin Panel', icon: Settings },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-64 bg-primary-900 text-white flex flex-col h-screen fixed left-0 top-0 z-20">
      <div className="px-6 py-5 border-b border-primary-800">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-600 rounded-lg">
            <Shield size={20} />
          </div>
          <div>
            <h1 className="font-bold text-sm leading-tight">LegalDoc</h1>
            <p className="text-xs text-primary-300">Analyzer</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ to, label, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            className={clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
              location.pathname === to
                ? 'bg-primary-700 text-white'
                : 'text-primary-200 hover:bg-primary-800 hover:text-white'
            )}
          >
            <Icon size={17} />
            {label}
          </Link>
        ))}

        {user?.role === 'admin' && (
          <>
            <div className="pt-3 pb-1 px-3">
              <p className="text-xs font-semibold text-primary-400 uppercase tracking-wider">Admin</p>
            </div>
            {adminItems.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                  location.pathname.startsWith(to)
                    ? 'bg-primary-700 text-white'
                    : 'text-primary-200 hover:bg-primary-800 hover:text-white'
                )}
              >
                <Icon size={17} />
                {label}
              </Link>
            ))}
          </>
        )}
      </nav>

      <div className="px-4 py-4 border-t border-primary-800">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-sm font-bold">
            {user?.full_name?.[0]?.toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.full_name}</p>
            <p className="text-xs text-primary-400 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-primary-300 hover:text-white hover:bg-primary-800 rounded-lg transition-colors"
        >
          <LogOut size={15} />
          Çıkış Yap
        </button>
      </div>
    </aside>
  )
}
