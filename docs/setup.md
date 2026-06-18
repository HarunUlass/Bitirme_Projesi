# Kurulum ve Geliştirme Kılavuzu

## Gereksinimler

| Araç | Versiyon |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| Tesseract OCR | İsteğe bağlı |

## 1. Gemini API Key Alma

1. https://aistudio.google.com/ adresine gidin
2. "Get API Key" → "Create API Key" tıklayın
3. Kopyalanan anahtarı `.env` dosyasına ekleyin

## 2. Backend Kurulumu

```bash
cd backend

# Sanal ortam oluştur
python -m venv venv

# Aktif et
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Ortam değişkenlerini ayarla
cp .env.example .env
# .env dosyasını açın ve GEMINI_API_KEY değerini girin

# Çalıştır
uvicorn app.main:app --reload --port 8000
```

İlk çalıştırmada:
- SQLite veritabanı otomatik oluşturulur
- Admin kullanıcısı oluşturulur: `admin@legaldoc.com` / `Admin123!`
- `uploads/` ve `chroma_db/` klasörleri oluşturulur

## 3. Frontend Kurulumu

```bash
cd frontend
npm install

# Geliştirme sunucusunu başlat
npm run dev
```

Tarayıcıda http://localhost:5173 adresini açın.

## 4. Tesseract OCR (İsteğe Bağlı)

Taranmış belgeler için:

**Windows:**
```
https://github.com/UB-Mannheim/tesseract/wiki
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-tur
```

**Mac:**
```bash
brew install tesseract
```

## Ortam Değişkenleri

| Değişken | Açıklama | Varsayılan |
|---------|---------|-----------|
| `SECRET_KEY` | JWT imzalama anahtarı | dev-key |
| `GEMINI_API_KEY` | Google AI Studio API key | — |
| `GEMINI_MODEL` | LLM modeli | gemini-1.5-pro |
| `GEMINI_FLASH_MODEL` | Hızlı model | gemini-1.5-flash |
| `GEMINI_EMBEDDING_MODEL` | Embedding modeli | models/text-embedding-004 |
| `DATABASE_URL` | SQLAlchemy URL | sqlite+aiosqlite:///./legal_doc_analyzer.db |
| `UPLOAD_DIR` | Dosya yükleme klasörü | ./uploads |
| `CHROMA_PERSIST_DIR` | ChromaDB klasörü | ./chroma_db |

## API Endpoint'leri

### Auth
- `POST /api/v1/auth/register` — Kayıt
- `POST /api/v1/auth/login` — Giriş
- `POST /api/v1/auth/refresh` — Token yenile
- `GET /api/v1/auth/me` — Mevcut kullanıcı

### Documents
- `GET /api/v1/documents/` — Doküman listesi
- `POST /api/v1/documents/upload` — Yükle
- `GET /api/v1/documents/{id}` — Detay
- `DELETE /api/v1/documents/{id}` — Sil
- `GET /api/v1/documents/{id}/download` — İndir

### Analysis
- `POST /api/v1/analysis/{doc_id}/start` — Analiz başlat
- `GET /api/v1/analysis/{doc_id}` — Sonuç getir

### Reports
- `GET /api/v1/reports/{doc_id}/pdf` — PDF rapor indir

### Admin
- `GET /api/v1/admin/users` — Kullanıcılar
- `GET /api/v1/admin/reference-contracts` — Referans listesi
- `POST /api/v1/admin/reference-contracts` — Ekle
- `DELETE /api/v1/admin/reference-contracts/{id}` — Sil

Swagger UI: http://localhost:8000/docs
