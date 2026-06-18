import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { authService } from '@/services/auth.service'
import { useAuthStore } from '@/store/authStore'
import { Shield } from 'lucide-react'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '' })

  const { mutate, isPending } = useMutation({
    mutationFn: () => authService.register(form.email, form.password, form.full_name),
    onSuccess: (data) => {
      setAuth(data.user, data.access_token, data.refresh_token)
      toast.success('Kayıt başarılı!')
      navigate('/')
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Kayıt başarısız'),
  })

  const field = (name: keyof typeof form) => ({
    value: form[name],
    onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((p) => ({ ...p, [name]: e.target.value })),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (form.password !== form.confirm) return toast.error('Şifreler eşleşmiyor')
    if (form.password.length < 6) return toast.error('Şifre en az 6 karakter olmalı')
    mutate()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-900 via-primary-800 to-primary-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="p-3 bg-primary-600 rounded-xl">
            <Shield size={28} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">LegalDoc</h1>
            <p className="text-sm text-gray-500">Analyzer</p>
          </div>
        </div>

        <h2 className="text-xl font-semibold text-gray-800 mb-6">Hesap Oluştur</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ad Soyad</label>
            <input type="text" className="input" placeholder="Ad Soyad" required {...field('full_name')} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input type="email" className="input" placeholder="ornek@email.com" required {...field('email')} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Şifre</label>
            <input type="password" className="input" placeholder="En az 6 karakter" required {...field('password')} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Şifre Tekrar</label>
            <input type="password" className="input" placeholder="••••••••" required {...field('confirm')} />
          </div>
          <button type="submit" disabled={isPending} className="btn-primary w-full py-2.5">
            {isPending ? 'Kayıt olunuyor...' : 'Kayıt Ol'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          Zaten hesabınız var mı?{' '}
          <Link to="/login" className="text-primary-600 font-medium hover:underline">
            Giriş Yap
          </Link>
        </p>
      </div>
    </div>
  )
}
