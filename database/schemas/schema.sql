-- LegalDoc Analyzer Veritabanı Şeması
-- SQLite / PostgreSQL uyumlu

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name   TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'user',  -- user | admin
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS documents (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename            TEXT NOT NULL,
    original_filename   TEXT NOT NULL,
    file_path           TEXT NOT NULL,
    file_size           INTEGER DEFAULT 0,
    file_type           TEXT,
    status              TEXT DEFAULT 'uploaded',  -- uploaded | text_extracted | indexed | error
    extracted_text      TEXT,
    page_count          INTEGER DEFAULT 0,
    is_reference        INTEGER NOT NULL DEFAULT 0,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME
);

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_is_reference ON documents(is_reference);

CREATE TABLE IF NOT EXISTS analyses (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id         INTEGER NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,
    status              TEXT DEFAULT 'pending',  -- pending | running | completed | error
    summary             TEXT,
    document_type       TEXT,
    parties             TEXT,   -- JSON
    key_dates           TEXT,   -- JSON
    clauses             TEXT,   -- JSON
    risk_flags          TEXT,   -- JSON
    similar_contracts   TEXT,   -- JSON
    compliance_score    REAL,
    overall_risk_level  TEXT DEFAULT 'low',
    recommendations     TEXT,   -- JSON
    raw_gemini_response TEXT,
    error_message       TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME
);

CREATE INDEX IF NOT EXISTS idx_analyses_document_id ON analyses(document_id);

CREATE TABLE IF NOT EXISTS annotations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id     INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    page_number     INTEGER DEFAULT 1,
    content         TEXT NOT NULL,
    annotation_type TEXT DEFAULT 'note',  -- note | highlight | flag
    color           TEXT DEFAULT '#FFEB3B',
    position        TEXT,   -- JSON {"x":..., "y":..., "width":..., "height":...}
    selected_text   TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME
);

CREATE INDEX IF NOT EXISTS idx_annotations_document_id ON annotations(document_id);
CREATE INDEX IF NOT EXISTS idx_annotations_user_id ON annotations(user_id);
