import api from './api'
import type { TokenResponse, User } from '@/types'

export const authService = {
  login: (email: string, password: string) =>
    api.post<TokenResponse>('/auth/login', { email, password }).then((r) => r.data),

  register: (email: string, password: string, full_name: string) =>
    api.post<TokenResponse>('/auth/register', { email, password, full_name }).then((r) => r.data),

  me: () => api.get<User>('/auth/me').then((r) => r.data),
}
