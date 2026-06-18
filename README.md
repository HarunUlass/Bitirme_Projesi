# LegalDoc Analyzer — Hukuki Doküman Analiz Sistemi

## Proje Tanımı

LegalDoc Analyzer, hukuki ve ticari dokümanların yapay zekâ destekli analizi için geliştirilmiş kapsamlı bir web platformudur. Kullanıcılar PDF, DOCX ve görsel formatlarındaki belgeleri yükleyerek otomatik metin çıkarma, Gemini LLM tabanlı hukuki analiz, TTK/TBK maddelerine dayalı risk tespiti, RAG tabanlı benzer sözleşme karşılaştırması ve detaylı PDF rapor üretimi gerçekleştirebilir.

Sistem, 6102 sayılı Türk Ticaret Kanunu (TTK) ve 6098 sayılı Türk Borçlar Kanunu (TBK) hükümlerine göre sözleşmeleri analiz eder; emredici hükümlere aykırılık, orantısız cezai şartlar, rekabet yasağı ihlalleri ve KVKK uyumsuzlukları gibi riskleri tespit eder.

## Kullanılan Teknolojiler

### Backend
| Teknoloji | Versiyon | Açıklama |
|-----------|----------|----------|
| **FastAPI** | 0.111.0 | Async Python web framework |
| **SQLAlchemy** | 2.0.30 (async) | ORM ve veritabanı yönetimi |
| **SQLite** (aiosqlite) | — | İlişkisel veritabanı |
| **JWT** (python-jose) | 3.3.0 | Kimlik doğrulama (access + refresh token) |
| **bcrypt** | 4.1.3 | Şifre hashleme |
| **ReportLab** | 4.2.0 | PDF rapor oluşturma (Türkçe TTF font desteği) |
| **Pydantic** | 2.7.1 | Veri validasyonu ve ayar yönetimi |
| **Uvicorn** | 0.29.0 | ASGI sunucusu |

### AI Module
| Teknoloji | Açıklama |
|-----------|----------|
| **Google Gemini 3.1 Flash Lite** | Doküman analizi, madde analizi, risk tespiti, özet üretimi |
| **Gemini Embedding (gemini-embedding-001)** | Vektör embedding üretimi |
| **ChromaDB** 0.5.3 | Vektör veritabanı (RAG pipeline + TTK madde indeksleme) |
| **pdfplumber** 0.11.0 | PDF metin çıkarma |
| **python-docx** 1.1.0 | DOCX metin çıkarma |
| **pytesseract + Pillow** | OCR desteği (taranmış belgeler ve görseller, Türkçe+İngilizce) |

### Frontend
| Teknoloji | Versiyon | Açıklama |
|-----------|----------|----------|
| **React** | 18.3 | UI framework |
| **TypeScript** | 5.2 | Tip güvenliği |
| **Vite** | 5.3 | Build aracı ve dev sunucusu |
| **Tailwind CSS** | 3.4 | Utility-first CSS framework |
| **TanStack Query** | 5.45 | Sunucu state yönetimi ve cache |
| **Zustand** | 4.5 | Client-side state yönetimi |
| **react-pdf** | 9.1 | PDF belge görüntüleme |
| **Axios** | 1.7 | HTTP client |
| **Lucide React** | — | İkon kütüphanesi |
| **react-hot-toast** | 2.4 | Bildirim sistemi |
| **react-dropzone** | 14.2 | Dosya sürükle-bırak yükleme |

### Altyapı
| Teknoloji | Açıklama |
|-----------|----------|
| **Docker & Docker Compose** | Konteynerleştirme ve servis orkestrasyonu |
| **python:3.11-slim** | Backend container base image |
| **node:20-alpine** | Frontend container base image |

## Sistem Mimarisi

```
┌──────────────────────────────────────────────────────────────────┐
│                     React Frontend (Vite + TypeScript)            │
│                                                                  │
│   LoginPage ─ RegisterPage ─ DashboardPage ─ DocumentPage        │
│   AnalysisPage ─ AdminPage ─ ReportPage                         │
│                                                                  │
│   Components:                                                    │
│   ├── Dashboard/    (DocumentCard, UploadArea)                   │
│   ├── Analysis/     (SummaryPanel, RiskPanel, ClauseAnalysis,    │
│   │                  ComparisonView)                             │
│   ├── DocumentViewer/ (PDFViewer, AnnotationPanel)               │
│   └── shared/       (Layout, Sidebar, LoadingSpinner)            │
└──────────────────────────┬───────────────────────────────────────┘
                           │  Vite Proxy → REST API (JSON)
┌──────────────────────────▼───────────────────────────────────────┐
│                      FastAPI Backend (:8000)                      │
│                                                                  │
│   /api/v1/auth        → Kayıt, giriş, token yenileme, profil    │
│   /api/v1/documents   → Doküman CRUD, metin çıkarma, annotation │
│   /api/v1/analysis    → Analiz başlatma, sonuç sorgulama         │
│   /api/v1/reports     → PDF rapor oluşturma ve indirme           │
│   /api/v1/admin       → Referans sözleşme yönetimi, TTK indeks, │
│                         kullanıcı listesi, diagnostik             │
│   /health             → Sağlık kontrolü                          │
│   /uploads            → Statik dosya servisi                     │
└──────────┬────────────────────────────┬──────────────────────────┘
           │                            │
┌──────────▼──────────────┐  ┌─────────▼──────────────────────────┐
│      AI Module           │  │          Veri Katmanı               │
│                          │  │                                    │
│  ┌─ gemini/              │  │  SQLite (legal_doc_analyzer.db)    │
│  │  ├── client.py        │  │  ├── users                        │
│  │  └── prompts.py       │  │  ├── documents                    │
│  │                       │  │  ├── analyses                     │
│  ├─ agents/              │  │  └── annotations                  │
│  │  └── document_agent   │  │                                    │
│  │                       │  │  ChromaDB (./chroma_db/)           │
│  ├─ rag/                 │  │  ├── legal_contracts (referans)    │
│  │  ├── pipeline.py      │  │  └── ttk_articles (TTK maddeleri) │
│  │  └── vector_store.py  │  │                                    │
│  │                       │  │  ./uploads/                        │
│  ├─ ocr/                 │  │  ├── {user_id}/  (kullanıcı dosya) │
│  │  ├── pdf_extractor    │  │  └── references/ (referans dosya)  │
│  │  ├── docx_extractor   │  └────────────────────────────────────┘
│  │  └── image_extractor  │
│  │                       │
│  └─ legal_knowledge_base │
│     (TTK PDF → maddeler  │
│      → ChromaDB RAG)     │
└──────────────────────────┘
```

## Özellikler

| Özellik | Açıklama |
|---------|----------|
| **Kimlik Doğrulama** | JWT tabanlı auth (access + refresh token), rol sistemi (user / admin) |
| **Kullanıcı Kaydı** | Email + şifre ile kayıt, otomatik token üretimi |
| **Doküman Yükleme** | PDF, DOCX, DOC, PNG, JPG, JPEG, TIFF, BMP, WEBP — max 50 MB |
| **Metin Çıkarma** | pdfplumber (PDF), python-docx (DOCX), pytesseract OCR (taranmış belgeler ve görseller) |
| **Gemini LLM Analizi** | Kapsamlı sözleşme özeti, taraf tespiti, önemli tarihler, madde analizi |
| **TTK/TBK Risk Tespiti** | 3 seviyeli risk sistemi (kritik / uyarı / bilgi) — kanun maddeleri referanslı |
| **Uyumluluk Skoru** | 0-100 arası TTK/TBK uyumluluk puanı ve genel risk seviyesi |
| **TTK Bilgi Tabanı** | TTK PDF'inden 600+ madde ayrıştırma, ChromaDB'ye vektör indeksleme, RAG ile ilgili madde getirme |
| **RAG Karşılaştırma** | Referans sözleşme kütüphanesi ile benzerlik analizi + AI destekli karşılaştırma |
| **Annotation** | Belge üzerinde not, işaretleme ve bayrak ekleme (sayfa bazlı) |
| **PDF Rapor** | Analiz sonuçlarını Türkçe karakter destekli PDF rapor olarak indirme |
| **PDF Görüntüleyici** | Uygulama içi react-pdf tabanlı belge görüntüleme |
| **Admin Paneli** | Referans sözleşme kütüphanesi yönetimi, TTK indeksleme kontrolü, kullanıcı listesi |
| **Referans Sözleşme Detay** | Referans sözleşmeleri görüntüleme, metin okuma ve indirme |
| **Otomatik TTK Yükleme** | Sunucu başlangıcında ChromaDB'deki TTK verisini otomatik tespit ve yükleme |
| **Docker Desteği** | Tek komutla çalışan Docker Compose ortamı |

## Kurulum

### Ön Koşullar
- **Docker & Docker Compose** (önerilen yöntem)
- veya manuel kurulum için:
  - Python 3.11+
  - Node.js 20+
  - Tesseract OCR (opsiyonel, taranmış belgeler için)
- **Gemini API Key** — [Google AI Studio](https://aistudio.google.com/)

---

### Yöntem 1: Docker ile Kurulum (Önerilen)

#### 1. Depoyu Klonlayın
```bash
git clone https://github.com/HarunUlass/Bitirme_Projesi/
cd Bitirme_Projesi
```

#### 2. Ortam Değişkenlerini Ayarlayın
Proje kök dizinindeki `.env` dosyasını düzenleyin:
```env
# Zorunlu
GEMINI_API_KEY=your-gemini-api-key-here

# Opsiyonel (varsayılan değerler mevcuttur)
SECRET_KEY=change-me-in-production
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_FLASH_MODEL=gemini-3.1-flash-lite
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001
```

#### 3. Docker ile Başlatın
```bash
docker-compose up -d --build
```

Bu komut iki container başlatır:
- **backend** → `http://localhost:8000` (FastAPI + AI Module)
- **frontend** → `http://localhost:5173` (React + Vite)

#### 4. Durumu Kontrol Edin
```bash
# Container'ları görüntüle
docker-compose ps

# Backend logları
docker-compose logs -f backend

# Sağlık kontrolü
curl http://localhost:8000/health
```

---

### Yöntem 2: Manuel Kurulum

#### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env dosyasını açın ve GEMINI_API_KEY değerini girin
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend, Vite proxy aracılığıyla `/api` ve `/uploads` isteklerini otomatik olarak backend'e yönlendirir.

---

### Varsayılan Admin Hesabı
İlk çalıştırmada otomatik oluşturulur:
- **Email:** `admin@legaldoc.com`
- **Şifre:** `Admin123!`

> ⚠️ Üretim ortamında bu şifreyi değiştirin.

## Kullanım Kılavuzu

### 1. Giriş ve Kayıt
Admin hesabıyla veya yeni kayıt oluşturarak giriş yapın.

### 2. TTK Bilgi Tabanı Kurulumu (Admin)
Admin panelindeki **TTK Bilgi Tabanı** sekmesinden:
1. **Adım 1:** "PDF'i Belleğe Yükle" → TTK PDF'ini okur ve ~600 maddeye ayırır
2. **Adım 2:** "İndekslemeyi Başlat" → Maddeleri Gemini embedding ile ChromaDB'ye indeksler

> Sunucu yeniden başlatıldığında, daha önce indekslenmiş veriler otomatik olarak yüklenir.

### 3. Referans Sözleşme Ekleme (Admin)
Admin panelindeki **Referans Sözleşmeler** sekmesinden PDF/DOCX formatında örnek sözleşmeler yükleyin. Bunlar RAG pipeline'a eklenerek karşılaştırma için kullanılır.

### 4. Doküman Yükleme ve Analiz
1. Dashboard'dan PDF, DOCX veya görsel formatında doküman yükleyin
2. Doküman detay sayfasından "Analiz Başlat" butonuna tıklayın
3. Analiz sonuçlarını 4 sekmede inceleyin:
   - **Özet** — Doküman özeti, taraflar, tarihler, uyumluluk skoru
   - **Riskler** — TTK/TBK referanslı risk bayrakları
   - **Maddeler** — Sözleşme maddelerinin hukuki analizi
   - **Karşılaştırma** — Referans sözleşmelerle benzerlik analizi

### 5. PDF Rapor İndirme
Tamamlanmış analizler için "PDF Rapor İndir" butonu ile detaylı analiz raporunu indirin.

### 6. Annotation (Not Ekleme)
Doküman görüntüleyicide belge sayfaları üzerine not, işaretleme ve bayrak ekleyin.

## API Endpoint'leri

### Kimlik Doğrulama (`/api/v1/auth`)
| Metod | Endpoint | Açıklama |
|-------|----------|----------|
| POST | `/register` | Yeni kullanıcı kaydı |
| POST | `/login` | Giriş (access + refresh token) |
| POST | `/refresh` | Token yenileme |
| GET | `/me` | Mevcut kullanıcı bilgileri |

### Dokümanlar (`/api/v1/documents`)
| Metod | Endpoint | Açıklama |
|-------|----------|----------|
| GET | `/` | Kullanıcının doküman listesi (sayfalı) |
| POST | `/upload` | Yeni doküman yükleme |
| GET | `/{id}` | Doküman detayı |
| DELETE | `/{id}` | Doküman silme |
| POST | `/{id}/retry-extraction` | Hatalı metin çıkarmayı yeniden dene |
| GET | `/{id}/download` | Doküman indirme |
| GET | `/{id}/annotations` | Annotation listesi |
| POST | `/{id}/annotations` | Yeni annotation ekleme |
| DELETE | `/{id}/annotations/{ann_id}` | Annotation silme |

### Analiz (`/api/v1/analysis`)
| Metod | Endpoint | Açıklama |
|-------|----------|----------|
| POST | `/{id}/start` | Analiz başlatma (`?force=true` ile yeniden analiz) |
| GET | `/{id}` | Analiz sonucu sorgulama |
| DELETE | `/{id}` | Analiz silme |

### Raporlar (`/api/v1/reports`)
| Metod | Endpoint | Açıklama |
|-------|----------|----------|
| GET | `/{id}/pdf` | PDF analiz raporu indirme |

### Admin (`/api/v1/admin`)
| Metod | Endpoint | Açıklama |
|-------|----------|----------|
| GET | `/users` | Kullanıcı listesi |
| GET | `/reference-contracts` | Referans sözleşme listesi |
| POST | `/reference-contracts` | Referans sözleşme yükleme |
| GET | `/reference-contracts/{id}` | Referans sözleşme detayı |
| GET | `/reference-contracts/{id}/download` | Referans sözleşme indirme |
| POST | `/reference-contracts/{id}/retry` | Hatalı sözleşmeyi yeniden işle |
| DELETE | `/reference-contracts/{id}` | Referans sözleşme silme |
| GET | `/reference-contracts/diagnostics` | ChromaDB ve dosya durumu kontrolü |
| POST | `/ttk/load` | TTK PDF'ini belleğe yükle |
| POST | `/ttk/index` | TTK maddelerini ChromaDB'ye indeksle |
| GET | `/ttk/status` | TTK bilgi tabanı durumu |

## Proje Yapısı

```
Bitirme_Projesi_v2/
├── .env                          # Docker Compose ortam değişkenleri
├── docker-compose.yml            # Servis tanımları (backend + frontend)
│
├── backend/
│   ├── Dockerfile                # Python 3.11-slim + Tesseract + DejaVu fonts
│   ├── requirements.txt          # Python bağımlılıkları
│   ├── .env.example              # Backend ortam değişkenleri şablonu
│   ├── legal_doc_analyzer.db     # SQLite veritabanı (otomatik oluşturulur)
│   ├── chroma_db/                # ChromaDB vektör deposu (persist)
│   ├── uploads/                  # Yüklenen dosyalar
│   │   ├── {user_id}/            # Kullanıcı dokümanları
│   │   └── references/           # Admin referans sözleşmeleri
│   └── app/
│       ├── main.py               # FastAPI uygulama giriş noktası, lifespan
│       ├── core/
│       │   ├── config.py         # Pydantic settings (tüm ayarlar)
│       │   ├── database.py       # SQLAlchemy async engine + session
│       │   └── security.py       # JWT oluşturma/doğrulama, bcrypt
│       ├── models/
│       │   ├── user.py           # User modeli (id, email, role, ...)
│       │   ├── document.py       # Document modeli (dosya bilgisi, is_reference)
│       │   ├── analysis.py       # Analysis modeli (analiz sonuçları JSON)
│       │   └── annotation.py     # Annotation modeli (sayfa notları)
│       ├── schemas/              # Pydantic request/response şemaları
│       ├── api/
│       │   ├── deps.py           # Dependency injection (auth, admin)
│       │   └── v1/
│       │       ├── auth.py       # Kayıt, giriş, token yenileme
│       │       ├── documents.py  # Doküman CRUD + annotation
│       │       ├── analysis.py   # Analiz başlatma/sorgulama
│       │       ├── reports.py    # PDF rapor oluşturma
│       │       └── admin.py      # Referans sözleşme + TTK yönetimi
│       └── services/
│           ├── document_service.py   # Metin çıkarma + RAG indeksleme
│           ├── analysis_service.py   # Gemini analiz orchestration
│           └── report_service.py     # ReportLab PDF rapor üretimi
│
├── ai-module/
│   ├── gemini/
│   │   ├── client.py             # Gemini API client (singleton, embed, generate)
│   │   └── prompts.py            # Analiz, risk, karşılaştırma, özet prompt'ları
│   ├── agents/
│   │   └── document_agent.py     # Ana analiz ajanı (analiz + risk + RAG)
│   ├── rag/
│   │   ├── pipeline.py           # RAG pipeline (add, search, remove)
│   │   └── vector_store.py       # ChromaDB wrapper (singleton client)
│   ├── ocr/
│   │   ├── ocr_processor.py      # Ana OCR yönlendirici
│   │   ├── pdf_extractor.py      # pdfplumber ile PDF metin çıkarma
│   │   ├── docx_extractor.py     # python-docx ile DOCX metin çıkarma
│   │   └── image_extractor.py    # pytesseract ile görsel OCR
│   ├── legal_knowledge_base.py   # TTK PDF → madde ayrıştırma → ChromaDB RAG
│   └── data/
│       └── TTK.pdf               # Türk Ticaret Kanunu PDF (~8.5 MB)
│
├── frontend/
│   ├── Dockerfile                # Node.js 20 Alpine
│   ├── package.json              # NPM bağımlılıkları
│   ├── vite.config.ts            # Vite yapılandırması + API proxy
│   ├── tailwind.config.js        # Tailwind CSS yapılandırması
│   └── src/
│       ├── App.tsx               # React Router (ProtectedRoute, AdminRoute)
│       ├── main.tsx              # React entry point (QueryClient, Toaster)
│       ├── index.css             # Global stiller
│       ├── types/index.ts        # TypeScript tip tanımları
│       ├── store/
│       │   └── authStore.ts      # Zustand auth state (persist)
│       ├── services/
│       │   ├── api.ts            # Axios instance + interceptor
│       │   ├── auth.service.ts   # Auth API çağrıları
│       │   ├── document.service.ts # Doküman API çağrıları
│       │   └── analysis.service.ts # Analiz + Admin API çağrıları
│       ├── pages/
│       │   ├── LoginPage.tsx     # Giriş sayfası
│       │   ├── RegisterPage.tsx  # Kayıt sayfası
│       │   ├── DashboardPage.tsx # Ana sayfa (doküman listesi + yükleme)
│       │   ├── DocumentPage.tsx  # Doküman detay + PDF görüntüleme
│       │   ├── AnalysisPage.tsx  # Analiz sonuçları (4 sekmeli)
│       │   ├── ReportPage.tsx    # Rapor sayfası
│       │   └── AdminPage.tsx     # Admin paneli (3 sekmeli)
│       └── components/
│           ├── Analysis/
│           │   ├── SummaryPanel.tsx    # Özet, taraflar, tarihler
│           │   ├── RiskPanel.tsx       # Risk bayrakları listesi
│           │   ├── ClauseAnalysis.tsx  # Madde analizi
│           │   └── ComparisonView.tsx  # Benzer sözleşme karşılaştırması
│           ├── Dashboard/
│           │   ├── DocumentCard.tsx    # Doküman kartı
│           │   └── UploadArea.tsx      # Drag & drop yükleme alanı
│           ├── DocumentViewer/
│           │   ├── PDFViewer.tsx       # react-pdf tabanlı görüntüleyici
│           │   └── AnnotationPanel.tsx # Not ekleme paneli
│           └── shared/
│               ├── Layout.tsx         # Sayfa düzeni (Sidebar + Outlet)
│               ├── Sidebar.tsx        # Sol menü navigasyonu
│               └── LoadingSpinner.tsx  # Yüklenme animasyonu
│
├── database/
│   ├── migrations/               # Veritabanı migration dosyaları
│   ├── schemas/                  # SQL şema tanımları
│   └── seeds/                    # Başlangıç verileri
│
└── docs/
    ├── architecture.md           # Mimari dokümantasyonu
    └── setup.md                  # Kurulum detayları
```

## Docker Yapılandırması

`docker-compose.yml` iki servis tanımlar:

| Servis | Port | Base Image | Açıklama |
|--------|------|------------|----------|
| **backend** | 8000 | python:3.11-slim | FastAPI + AI Module + Tesseract OCR + DejaVu fonts |
| **frontend** | 5173 | node:20-alpine | React + Vite dev sunucusu |

**Docker Volume'lar:**
- `uploads_data` → Yüklenen dosyalar (`/app/uploads`)
- `chroma_data` → ChromaDB vektör deposu (`/app/chroma_db`)

## Ortam Değişkenleri

| Değişken | Zorunlu | Varsayılan | Açıklama |
|----------|---------|------------|----------|
| `GEMINI_API_KEY` | ✅ | — | Google AI Studio API anahtarı |
| `SECRET_KEY` | ✅ | `dev-secret-key...` | JWT imzalama anahtarı |
| `GEMINI_MODEL` | — | `gemini-3.1-flash-lite` | Ana analiz modeli |
| `GEMINI_FLASH_MODEL` | — | `gemini-3.1-flash-lite` | Hızlı özet modeli |
| `GEMINI_EMBEDDING_MODEL` | — | `models/gemini-embedding-001` | Embedding modeli |
| `DATABASE_URL` | — | `sqlite+aiosqlite:///./legal_doc_analyzer.db` | Veritabanı bağlantı dizesi |
| `UPLOAD_DIR` | — | `./uploads` | Dosya yükleme dizini |
| `CHROMA_PERSIST_DIR` | — | `./chroma_db` | ChromaDB persist dizini |
| `LEGAL_REFERENCE_PDF` | — | `/app/ai-module/data/TTK.pdf` | TTK PDF dosya yolu |
| `ALLOWED_ORIGINS` | — | `localhost:5173, localhost:3000` | CORS izinli origin'ler |

## Demo Açıklaması

LegalDoc Analyzer'ın tipik bir kullanım senaryosu aşağıdaki adımlarla ilerler:

### Adım 1 — Sisteme Giriş
`http://localhost:5173` adresine gidin. Varsayılan admin hesabıyla (`admin@legaldoc.com` / `Admin123!`) veya yeni bir hesap oluşturarak giriş yapın.

### Adım 2 — TTK Bilgi Tabanı Hazırlama (Admin — Tek Seferlik)
Sol menüden **Admin Paneli**'ne gidin, **TTK Bilgi Tabanı** sekmesini açın:
1. **"PDF'i Belleğe Yükle"** butonuna tıklayın → Sistem `TTK.pdf`'i okuyup ~600+ maddeye ayırır
2. **"İndekslemeyi Başlat"** butonuna tıklayın → Maddeler Gemini Embedding API ile vektöre çevrilip ChromaDB'ye kaydedilir

> Bu işlem bir kez yapılır. Sunucu yeniden başlatıldığında veriler otomatik yüklenir.

### Adım 3 — Referans Sözleşme Ekleme (Admin — Opsiyonel)
**Admin Paneli → Referans Sözleşmeler** sekmesinden örnek sözleşmeler (PDF/DOCX) yükleyin. Sistem bu sözleşmeleri RAG vektör veritabanına ekler; analiz sırasında yüklenen belgelerle karşılaştırma için kullanılır.

### Adım 4 — Belge Yükleme
Dashboard'da sürükle-bırak alanına ya da **"Dosya Seç"** butonu ile bir sözleşme (PDF, DOCX, görsel) yükleyin. Sistem arka planda:
- Dosyayı diske kaydeder
- pdfplumber / python-docx / OCR ile metni çıkarır
- Belge durumunu `text_extracted` olarak günceller

### Adım 5 — Analiz Başlatma
Belge detay sayfasından **"Analiz Başlat"** butonuna tıklayın. Arka planda şu işlemler çalışır:
1. RAG ile belgede geçen konulara ait TTK maddeleri ChromaDB'den getirilir
2. `DOCUMENT_ANALYSIS_PROMPT` → Gemini API → Özet, taraflar, maddeler, ilk risk bayrakları
3. `RISK_ANALYSIS_PROMPT` → Gemini API → Odaklanmış risk tespiti (TTK/TBK referanslı)
4. `COMPARISON_PROMPT` → Benzer referans sözleşmelerle karşılaştırma
5. Tüm sonuçlar veritabanına yazılır

### Adım 6 — Analiz Sonuçlarını İnceleme
Analiz tamamlandığında 4 sekmeli sonuç ekranı açılır:

| Sekme | İçerik |
|-------|--------|
| **Özet** | Belge türü, taraflar, önemli tarihler, uyumluluk skoru (0-100), genel risk seviyesi |
| **Riskler** | Kritik / Uyarı / Bilgi seviyeli risk bayrakları, ilgili TTK/TBK madde numaraları |
| **Maddeler** | Her sözleşme maddesinin hukuki analizi ve risk değerlendirmesi |
| **Karşılaştırma** | Referans sözleşmelerle benzerlik yüzdesi ve AI destekli fark analizi |

### Adım 7 — PDF Raporu İndirme
**"PDF Rapor İndir"** butonuna tıklayın. ReportLab ile oluşturulan, Türkçe karakter destekli, A4 formatında profesyonel analiz raporu indirilir. Rapor; özet, taraflar, risk tablosu, madde analizi ve öneriler bölümlerini içerir.

### Adım 8 — Belge Üzerine Not Ekleme (Opsiyonel)
Doküman görüntüleyicide belge sayfaları üzerine not, işaretleme ve bayrak eklenebilir.

---

## Lisans

Bu proje bitirme projesi kapsamında geliştirilmiştir.
