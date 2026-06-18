-- Varsayılan admin kullanıcısı seed
-- Şifre: Admin123!  (bcrypt hash)
-- NOT: Bu hash backend'de generate edilmiştir.
-- Üretim ortamında bu şifreyi değiştirin!

-- Backend ilk çalışmada otomatik olarak admin oluşturur.
-- Manuel olarak eklemek için:

-- INSERT OR IGNORE INTO users (email, hashed_password, full_name, role, is_active)
-- VALUES (
--   'admin@legaldoc.com',
--   '$2b$12$...',  -- python -c "from passlib.context import CryptContext; print(CryptContext(['bcrypt']).hash('Admin123!'))"
--   'Admin',
--   'admin',
--   1
-- );
