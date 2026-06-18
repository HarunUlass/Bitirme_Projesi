-- Migration 001: Başlangıç şeması
-- Tüm temel tabloları oluşturur

-- Bu migration içeriği database/schemas/schema.sql ile aynıdır.
-- SQLAlchemy async engine otomatik olarak tabloları oluşturur.
-- Manuel migration için bu dosyayı çalıştırın:
--   sqlite3 legal_doc_analyzer.db < database/migrations/001_initial.sql

-- users tablosu
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- documents tablosu
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    file_type TEXT,
    status TEXT DEFAULT 'uploaded',
    extracted_text TEXT,
    page_count INTEGER DEFAULT 0,
    is_reference INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- analyses tablosu
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL UNIQUE,
    status TEXT DEFAULT 'pending',
    summary TEXT,
    document_type TEXT,
    parties TEXT,
    key_dates TEXT,
    clauses TEXT,
    risk_flags TEXT,
    similar_contracts TEXT,
    compliance_score REAL,
    overall_risk_level TEXT DEFAULT 'low',
    recommendations TEXT,
    raw_gemini_response TEXT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- annotations tablosu
CREATE TABLE IF NOT EXISTS annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    page_number INTEGER DEFAULT 1,
    content TEXT NOT NULL,
    annotation_type TEXT DEFAULT 'note',
    color TEXT DEFAULT '#FFEB3B',
    position TEXT,
    selected_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
