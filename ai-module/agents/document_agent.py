import json
import re
import logging
from gemini.client import GeminiClient
from gemini.prompts import DOCUMENT_ANALYSIS_PROMPT, COMPARISON_PROMPT, QUICK_SUMMARY_PROMPT, RISK_ANALYSIS_PROMPT
from rag.pipeline import RAGPipeline
from legal_knowledge_base import LegalKnowledgeBase

logger = logging.getLogger(__name__)

# Risk analizi sorgusunda kullanılan anahtar terimler.
# Bunlar ChromaDB'den daha alakalı TTK/TBK maddeleri getirmek için sorguya eklenir.
_RISK_QUERY_KEYWORDS = (
    "cezai şart fesih sorumluluk tazminat rekabet yasağı gizlilik KVKK "
    "zamanaşımı temerrüt faiz emredici hüküm kesin hükümsüzlük gabin "
    "aşırı ifa güçlüğü sorumluluk sınırlandırma iş güvencesi"
)


class DocumentAgent:
    def __init__(self):
        self.client = GeminiClient.get()
        self.rag = RAGPipeline()
        self.kb = LegalKnowledgeBase.get()

    def analyze(self, text: str, filename: str) -> dict:
        if not text or len(text.strip()) < 50:
            raise ValueError("Doküman metni çok kısa veya boş")

        truncated = text[:100_000]

        # 1. Genel analiz için ilgili TTK maddelerini getir
        if self.kb.is_loaded():
            relevant_articles = self.kb.get_relevant_articles(truncated)
            logger.info("TTK'dan %d karakterlik ilgili madde metni getirildi.", len(relevant_articles))
        else:
            relevant_articles = "TTK PDF yüklenemedi — genel hukuki bilgi ile analiz yapılacak."
            logger.warning("TTK PDF yüklü değil, genel bilgiyle analiz yapılacak.")

        # 2. Genel belge analizi: özet, taraflar, maddeler, ilk risk bayrakları
        prompt = DOCUMENT_ANALYSIS_PROMPT.format(
            text=truncated,
            relevant_legal_articles=relevant_articles,
        )
        raw = self.client.generate(prompt)
        result = self._parse_json(raw)

        # 3. Odaklanmış risk analizi: risk anahtar terimleriyle TTK'dan ek maddeler getir
        if self.kb.is_loaded():
            risk_query = _RISK_QUERY_KEYWORDS + "\n\n" + truncated[:2000]
            risk_articles = self.kb.get_relevant_articles(risk_query, top_k=10)
        else:
            risk_articles = relevant_articles

        try:
            risk_prompt = RISK_ANALYSIS_PROMPT.format(
                text=truncated[:50_000],
                relevant_legal_articles=risk_articles,
            )
            risk_raw = self.client.generate(risk_prompt)
            risk_result = self._parse_json(risk_raw)

            # Genel analizde bulunan risk başlıklarını kaydet (duplicate engeli)
            existing_titles = {f.get("title", "").lower() for f in result.get("risk_flags", [])}
            for flag in risk_result.get("risk_flags", []):
                if flag.get("title", "").lower() not in existing_titles:
                    result.setdefault("risk_flags", []).append(flag)
                    existing_titles.add(flag.get("title", "").lower())

            # Odaklanmış analizin compliance_score ve overall_risk_level'ı daha güvenilir
            if risk_result.get("compliance_score") is not None:
                result["compliance_score"] = risk_result["compliance_score"]
            if risk_result.get("overall_risk_level"):
                result["overall_risk_level"] = risk_result["overall_risk_level"]

        except Exception as e:
            logger.warning("Odaklanmış risk analizi başarısız, genel analiz sonuçları kullanılıyor: %s", e)

        # RAG ile benzer sözleşmeleri bul ve AI karşılaştırması yap
        target_summary = result.get("summary", text[:500])
        try:
            similar = self.rag.search(text=text[:3000], n_results=5)

            # Sadece DB'de hâlâ indexed olan referans sözleşmeleri tut
            similar = self._filter_indexed_contracts(similar)

            enriched = []
            for match in similar:
                enriched_match = {
                    "doc_id": match["doc_id"],
                    "filename": match["filename"],
                    "score": match["score"],
                    "summary": match["summary"],
                }
                # AI karşılaştırması: sadece yüksek benzerlikli eşleşmeler için
                if match["score"] >= 0.4:
                    try:
                        ref_text = match.get("raw_text") or match.get("summary", "")
                        comp_prompt = COMPARISON_PROMPT.format(
                            target_summary=target_summary[:1500],
                            reference_summary=ref_text[:1500],
                        )
                        comparison_text = self.client.generate(comp_prompt)
                        enriched_match["comparison"] = comparison_text.strip()
                    except Exception:
                        enriched_match["comparison"] = None
                else:
                    enriched_match["comparison"] = None
                enriched.append(enriched_match)
            result["similar_contracts"] = enriched
        except Exception:
            result["similar_contracts"] = []

        return result

    def _filter_indexed_contracts(self, similar: list[dict]) -> list[dict]:
        """RAG sonuçlarını DB'deki indexed referans sözleşmelerle filtrele."""
        if not similar:
            return similar
        try:
            import sqlite3
            import os
            db_path = os.environ.get(
                "DATABASE_PATH",
                os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend/legal_doc_analyzer.db")),
            )
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            doc_ids = [str(m["doc_id"]) for m in similar]
            placeholders = ",".join("?" for _ in doc_ids)
            cursor.execute(
                f"SELECT id FROM documents WHERE id IN ({placeholders}) "
                f"AND is_reference = 1 AND status = 'indexed'",
                [int(d) for d in doc_ids],
            )
            valid_ids = {str(row[0]) for row in cursor.fetchall()}
            conn.close()
            filtered = [m for m in similar if str(m["doc_id"]) in valid_ids]
            if len(filtered) < len(similar):
                logger.info(
                    "RAG sonuçlarından %d/%d sözleşme filtrelendi (silinmiş veya indexlenmemiş).",
                    len(similar) - len(filtered), len(similar),
                )
            return filtered
        except Exception as e:
            logger.warning("Indexed filtresi uygulanamadı: %s", e)
            return similar

    def _parse_json(self, raw: str) -> dict:
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                return json.loads(match.group())
            raise ValueError(f"Gemini yanıtı JSON parse edilemedi: {raw[:200]}")
