# Sistem Mimarisi

## Genel Bakış

```
┌──────────────────────────────────────────────────────────┐
│  React Frontend (Vite + TypeScript)                       │
│  Port: 5173                                               │
│                                                           │
│  Pages: Login, Register, Dashboard, Document, Analysis,   │
│         Report, Admin                                     │
│  Store: Zustand (auth, document)                          │
│  HTTP:  Axios + TanStack Query                            │
└────────────────────────┬─────────────────────────────────┘
                         │ REST API
                         │ Proxy: /api → localhost:8000
┌────────────────────────▼─────────────────────────────────┐
│  FastAPI Backend                                           │
│  Port: 8000                                               │
│                                                           │
│  /api/v1/auth       — JWT login/register/refresh          │
│  /api/v1/documents  — Upload, list, delete, annotations   │
│  /api/v1/analysis   — Start, get, delete analysis         │
│  /api/v1/reports    — PDF rapor download                  │
│  /api/v1/admin      — Referans sözleşme + kullanıcı yön.  │
│  /uploads           — Static file serving                 │
└──────────┬──────────────────────────┬────────────────────┘
           │ Python import            │ SQLAlchemy async
           │ (sys.path)               │
┌──────────▼──────────┐   ┌──────────▼──────────────────┐
│   AI Module          │   │   SQLite Database            │
│   ai-module/         │   │   legal_doc_analyzer.db      │
│                      │   │                              │
│   gemini/            │   │   users                      │
│     client.py        │   │   documents                  │
│     prompts.py       │   │   analyses                   │
│                      │   │   annotations                │
│   ocr/               │   └─────────────────────────────┘
│     pdf_extractor    │
│     docx_extractor   │   ┌──────────────────────────────┐
│     ocr_processor    │   │   ChromaDB                   │
│                      │   │   chroma_db/                 │
│   agents/            │   │                              │
│     document_agent   │   │   Collection: legal_contracts │
│                      │   │   Embedding: text-embedding-004│
│   rag/               ├───►   Similarity: cosine         │
│     vector_store     │   └──────────────────────────────┘
│     pipeline         │
└─────────────────────┘
```

## Veri Akışı

### Doküman Yükleme
1. Frontend → POST /api/v1/documents/upload
2. Backend dosyayı ./uploads/{user_id}/{uuid}.pdf kaydeder
3. BackgroundTask: OCRProcessor.extract() → PDF/DOCX metin çıkarma
4. Document.status = "text_extracted"

### Analiz
1. Frontend → POST /api/v1/analysis/{doc_id}/start
2. BackgroundTask: DocumentAgent.analyze(text, filename)
3. Gemini 1.5 Pro → JSON analiz (özet, maddeler, riskler)
4. RAGPipeline.search(text) → ChromaDB benzer sözleşmeler
5. Analysis.status = "completed"

### Referans Sözleşme Ekleme (Admin)
1. Admin → POST /api/v1/admin/reference-contracts
2. BackgroundTask: OCR + RAGPipeline.add_document()
3. Gemini embedding → ChromaDB'ye kaydet
4. Document.status = "indexed"

### RAG Pipeline
1. Yeni doküman analiz edilirken text[:3000] embed edilir
2. ChromaDB cosine similarity ile en yakın 5 dokümanı döner
3. Sonuçlar analysis.similar_contracts alanına kaydedilir

## Güvenlik

- JWT access token (1 saat)
- JWT refresh token (7 gün)
- bcrypt şifre hashing
- CORS whitelist
- Kullanıcılar yalnızca kendi dokümanlarına erişebilir
- Admin endpoint'leri role kontrolü gerektirir
