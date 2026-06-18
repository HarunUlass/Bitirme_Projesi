"""
TTK (Türk Ticaret Kanunu) PDF Bilgi Tabanı — Singleton.

PDF bir kez okunur, maddelere ayrılır ve ChromaDB'ye indekslenir.
Her analiz sorgusunda yalnızca ilgili maddeler RAG ile getirilir.
"""

import os
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LegalKnowledgeBase:
    """Singleton: TTK PDF'ini okur, maddelere ayırır, ChromaDB'de saklar."""

    _instance: Optional["LegalKnowledgeBase"] = None

    def __init__(self):
        self._articles: dict[str, str] = {}
        self._full_text: str = ""
        self._loaded: bool = False
        self._indexed: bool = False
        self._page_count: int = 0

    # ------------------------------------------------------------------ #
    #  Singleton
    # ------------------------------------------------------------------ #
    @classmethod
    def get(cls) -> "LegalKnowledgeBase":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ #
    #  PDF Okuma
    # ------------------------------------------------------------------ #
    def load_pdf(self, pdf_path: str, force: bool = False) -> None:
        """PDF'i oku ve maddelere ayır. Zaten yüklüyse atla (force=True ile yeniden yükle)."""
        if self._loaded and not force:
            logger.info("TTK PDF zaten bellekte, tekrar yükleme atlanıyor.")
            return

        if not os.path.exists(pdf_path):
            logger.error("TTK PDF bulunamadı: %s", pdf_path)
            return

        logger.info("TTK PDF yükleniyor: %s", pdf_path)

        try:
            import pdfplumber

            text_parts: list[str] = []
            with pdfplumber.open(pdf_path) as pdf:
                self._page_count = len(pdf.pages)
                logger.info("TTK PDF sayfa sayısı: %d", self._page_count)
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                    else:
                        logger.debug("Sayfa %d boş metin döndürdü, atlanıyor.", i + 1)

            self._full_text = "\n\n".join(text_parts)
            logger.info(
                "TTK PDF'den %d/%d sayfa metin çıkarıldı, toplam %d karakter",
                len(text_parts), self._page_count, len(self._full_text),
            )
            self._articles = self._parse_articles(self._full_text)
            self._loaded = True

            if force:
                self._indexed = False

            logger.info(
                "TTK PDF yüklendi — %d madde bulundu",
                len(self._articles),
            )
        except Exception as e:
            logger.error("TTK PDF okuma hatası: %s", e)

    # ------------------------------------------------------------------ #
    #  Madde Ayrıştırma
    # ------------------------------------------------------------------ #
    def _parse_articles(self, text: str) -> dict[str, str]:
        """Metni bireysel maddelere ayır."""
        articles: dict[str, str] = {}

        # --- Metin ön işleme ---
        # MADDE ile sayı arasına giren satır sonlarını temizle
        normalized = re.sub(r'(?i)(MADDE)\s*\n+\s*(\d+)', r'\1 \2', text)
        # Fazla yatay boşlukları tek boşluğa indir (satır sonları hariç)
        normalized = re.sub(r'[^\S\n]+', ' ', normalized)

        # --- Madde başlıklarını bul ---
        # Ana kalıp: Satır başı zorunluluğu yok — PDF çıkarımında madde satır
        # ortasında kalabiliyor.  Tire/çizgi zorunlu tutularak metin-içi
        # referanslar ("Madde 5'e göre …") dışarıda bırakılıyor.
        pattern = r"((?:MADDE)\s+(\d+))\s*[-–—]"
        matches = list(re.finditer(pattern, normalized, re.IGNORECASE))

        # Fallback: tire olmadan, satır başıyla dene (bazı PDF'lerde tire kaybolabilir)
        if len(matches) < 100:
            pattern_alt = r"(?:^|\n)\s*((?:MADDE)\s+(\d+))\s*[-–—./:]?"
            alt_matches = list(re.finditer(pattern_alt, normalized, re.MULTILINE | re.IGNORECASE))
            if len(alt_matches) > len(matches):
                matches = alt_matches

        if not matches:
            # Fallback: tek büyük chunk olarak tut
            logger.warning("Madde ayrıştırma başarısız — tüm metin tek chunk olarak saklanacak.")
            articles["TTK_FULL"] = normalized
            return articles

        logger.info("Regex ile %d madde eşleşmesi bulundu.", len(matches))

        for i, match in enumerate(matches):
            article_num = match.group(2)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(normalized)
            article_text = normalized[start:end].strip()
            key = f"Madde {article_num}"

            # Aynı numaradan birden fazla varsa (tekrar baskılar), birleştir
            if key in articles:
                articles[key] += "\n" + article_text
            else:
                articles[key] = article_text
        return articles

    # ------------------------------------------------------------------ #
    #  ChromaDB İndeksleme
    # ------------------------------------------------------------------ #
    def index_to_vectorstore(self, on_progress=None) -> None:
        """Tüm maddeleri ChromaDB'ye batch embedding ile indeksle. Kaldığı yerden devam eder."""
        if self._indexed:
            return
        if not self._loaded:
            logger.warning("PDF yüklenmeden indeksleme yapılamaz.")
            return

        from rag.vector_store import VectorStore
        from gemini.client import GeminiClient
        import time

        store = VectorStore(collection_name="ttk_articles")
        client = GeminiClient.get()

        existing_ids = set(store.collection.get(include=[])["ids"])
        items = [(k, v) for k, v in self._articles.items() if k not in existing_ids]
        total = len(self._articles)

        if not items:
            logger.info("TTK maddeleri zaten tam indeksli (%d kayıt), atlanıyor.", len(existing_ids))
            self._indexed = True
            if on_progress:
                on_progress(total, total, 0)
            return

        logger.info(
            "TTK indeksleme başlıyor — %d madde (%d zaten mevcut, %d kaldı)...",
            total, len(existing_ids), len(items),
        )
        if on_progress:
            on_progress(len(existing_ids), total, 0)

        BATCH_SIZE = 5
        indexed = len(existing_ids)
        skipped = 0

        for batch_start in range(0, len(items), BATCH_SIZE):
            batch = items[batch_start: batch_start + BATCH_SIZE]
            keys = [k for k, _ in batch]
            texts = [v for _, v in batch]

            success = False
            for retry in range(5):
                try:
                    embeddings = client.embed_batch(texts)
                    for key, text, embedding in zip(keys, texts, embeddings):
                        store.add(
                            doc_id=key,
                            embedding=embedding,
                            text=text,
                            metadata={"article": key, "source": "TTK"},
                        )
                    indexed += len(batch)
                    success = True
                    break
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "quota" in err_str.lower():
                        wait = 10 * (2 ** retry)  # 10, 20, 40, 80, 160 sn
                        logger.info(
                            "Rate limit — %d sn bekleniyor... (batch %d/%d)",
                            wait, batch_start // BATCH_SIZE + 1, -(-len(items) // BATCH_SIZE),
                        )
                        time.sleep(wait)
                    else:
                        logger.warning("Batch indekslenemedi (%s): %s", keys[0], e)
                        skipped += len(batch)
                        break

            if not success and skipped < len(batch):
                skipped += len(batch)

            if on_progress:
                on_progress(indexed, total, skipped)
            logger.info(
                "İndeksleme ilerleme: %d / %d indekslendi (atlandı: %d)",
                indexed, total, skipped,
            )
            time.sleep(5.0)

        self._indexed = True
        logger.info(
            "TTK indeksleme tamamlandı — %d başarılı, %d atlandı / toplam %d madde.",
            indexed - len(existing_ids), skipped, total,
        )

    # ------------------------------------------------------------------ #
    #  RAG: İlgili Maddeleri Getir
    # ------------------------------------------------------------------ #
    def get_relevant_articles(self, document_text: str, top_k: int = 15) -> str:
        """Belge metnine en alakalı TTK maddelerini RAG ile getir."""
        from rag.vector_store import VectorStore
        from gemini.client import GeminiClient

        store = VectorStore(collection_name="ttk_articles")

        if store.count() == 0:
            logger.warning("TTK vektör deposu boş, fallback kullanılıyor.")
            return self._get_fallback_text()

        client = GeminiClient.get()
        query_embedding = client.embed_query(document_text[:3000])
        results = store.query(embedding=query_embedding, n_results=min(top_k, store.count()))

        if not results or not results["ids"] or not results["ids"][0]:
            return self._get_fallback_text()

        articles: list[str] = []
        separator = "\n" + "═" * 60 + "\n"

        for i in range(len(results["ids"][0])):
            article_id = results["ids"][0][i]
            article_text = results["documents"][0][i]
            distance = results["distances"][0][i]
            score = 1 - distance

            if score < 0.15:
                continue

            articles.append(
                f"📌 {article_id} (benzerlik: {score:.2f})\n{article_text}"
            )

        if not articles:
            return self._get_fallback_text()

        header = (
            "AŞAĞIDAKİ MADDELER, ANALİZ EDİLEN BELGEYE EN ALAKALI TÜRK TİCARET KANUNU (TTK) "
            "MADDELERİDİR. BU GERÇEK KANUN METİNLERİNE GÖRE RİSK ANALİZİ YAP:\n"
        )
        return header + separator + separator.join(articles)

    # ------------------------------------------------------------------ #
    #  Yardımcı
    # ------------------------------------------------------------------ #
    def _get_fallback_text(self) -> str:
        """Vektör deposu boşsa ham metinden ilk 20 maddeyi döndür."""
        if not self._articles:
            return "TTK maddeleri yüklenemedi."

        parts = []
        for key, text in list(self._articles.items())[:20]:
            parts.append(f"📌 {key}\n{text[:1000]}")
        return "\n\n".join(parts)

    def is_loaded(self) -> bool:
        return self._loaded

    def is_indexed(self) -> bool:
        return self._indexed

    def get_article_count(self) -> int:
        return len(self._articles)

    def get_page_count(self) -> int:
        return self._page_count

    def get_article(self, article_num: int) -> Optional[str]:
        """Belirli bir madde numarasını getir."""
        return self._articles.get(f"Madde {article_num}")
