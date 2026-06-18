import { create } from 'zustand'
import type { Document } from '@/types'

interface DocumentState {
  selected: Document | null
  setSelected: (doc: Document | null) => void
}

export const useDocumentStore = create<DocumentState>()((set) => ({
  selected: null,
  setSelected: (doc) => set({ selected: doc }),
}))
