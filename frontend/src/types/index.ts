export interface User {
  id: number
  email: string
  full_name: string
  role: 'user' | 'admin'
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface Document {
  id: number
  filename: string
  original_filename: string
  file_size: number
  file_type: string
  status: 'uploaded' | 'text_extracted' | 'indexed' | 'error'
  page_count: number
  is_reference: boolean
  created_at: string
  has_analysis: boolean
  file_url?: string
}

export interface DocumentListResponse {
  items: Document[]
  total: number
  page: number
  size: number
}

export interface RiskFlag {
  level: 'critical' | 'warning' | 'info'
  title: string
  description: string
  clause?: string
  legal_reference?: string
}

export interface Clause {
  title: string
  content: string
  analysis?: string
  risk_level?: 'low' | 'medium' | 'high' | 'critical'
  legal_reference?: string
}

export interface SimilarContract {
  doc_id: string
  filename: string
  score: number
  summary?: string
  comparison?: string
}

export interface Analysis {
  id: number
  document_id: number
  status: 'pending' | 'running' | 'completed' | 'error'
  summary?: string
  document_type?: string
  parties?: Array<{ role: string; name: string }>
  key_dates?: Array<{ label: string; date: string }>
  clauses?: Clause[]
  risk_flags?: RiskFlag[]
  similar_contracts?: SimilarContract[]
  compliance_score?: number
  overall_risk_level?: 'low' | 'medium' | 'high' | 'critical'
  recommendations?: string[]
  error_message?: string
  created_at: string
  updated_at?: string
}

export interface Annotation {
  id: number
  page_number: number
  content: string
  annotation_type: 'note' | 'highlight' | 'flag'
  color: string
  position?: { x: number; y: number; width: number; height: number }
  selected_text?: string
  created_at: string
}
