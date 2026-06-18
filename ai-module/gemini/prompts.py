DOCUMENT_ANALYSIS_PROMPT = """
Sen Türkiye'de uzmanlaşmış, deneyimli bir hukuk analistisin. Aşağıdaki hukuki/ticari dokümanı
6102 sayılı Türk Ticaret Kanunu (TTK) ve 6098 sayılı Türk Borçlar Kanunu (TBK) hükümlerine göre
detaylıca analiz et.

DOKÜMAN:
{text}

Lütfen aşağıdaki JSON formatında yanıt ver (başka açıklama ekleme, sadece JSON):

{{
  "summary": "Dokümanın kapsamlı Türkçe özeti (3-5 paragraf). TTK/TBK açısından genel değerlendirme içermeli.",
  "document_type": "sözleşme türü (örn: İş Sözleşmesi, Kira Sözleşmesi, NDA, Hizmet Sözleşmesi, Ortaklık Sözleşmesi, vs.)",
  "parties": [
    {{"role": "tarafın rolü", "name": "tarafın adı/ünvanı"}}
  ],
  "key_dates": [
    {{"label": "tarih açıklaması", "date": "tarih değeri"}}
  ],
  "clauses": [
    {{
      "title": "madde başlığı",
      "content": "madde özeti",
      "analysis": "maddenin TTK/TBK hükümlerine göre hukuki analizi ve önemi",
      "risk_level": "low|medium|high|critical",
      "legal_reference": "İlgili TTK/TBK madde numaraları (örn: TTK m.18, TBK m.27)"
    }}
  ],
  "risk_flags": [
    {{
      "level": "critical|warning|info",
      "title": "risk başlığı",
      "description": "riskin TTK/TBK çerçevesinde detaylı açıklaması",
      "clause": "ilgili sözleşme maddesi (varsa)",
      "legal_reference": "İlgili TTK/TBK kanun maddeleri (örn: TTK m.18, TBK m.27, TTK m.55)"
    }}
  ],
  "compliance_score": 75,
  "overall_risk_level": "low|medium|high|critical",
  "recommendations": [
    "TTK/TBK hükümlerine dayalı öneri 1",
    "öneri 2"
  ]
}}

═══════════════════════════════════════════════════════════════
İLGİLİ KANUN MADDELERİ (TTK PDF'inden otomatik getirilmiştir)
═══════════════════════════════════════════════════════════════

{relevant_legal_articles}

═══════════════════════════════════════════════════════════════
ÖNEMLİ DEĞERLENDİRME KRİTERLERİ
═══════════════════════════════════════════════════════════════

1. Emredici hükümlere aykırılık: Kanunun emredici hükümlerine aykırı maddeler kesin hükümsüzdür
2. Tek taraflı dezavantajlı maddeler: Taraflardan birini aşırı dezavantajlı konuma düşüren hükümler
3. Cezai şart orantılılığı: Aşırı cezai şartlar (TBK m.182 – hakim indirimi)
4. Fesih koşulları: Haksız fesih hükümleri, bildirim süreleri
5. Gizlilik ve KVKK uyumu: Kişisel verilerin korunması yükümlülükleri
6. Rekabet yasağı sınırları: TTK m.395-396, İK m.23 - süre, yer, konu bakımından
7. Zamanaşımı süreleri: Sözleşmedeki sürelerin kanuni sürelerle uyumu
8. Temerrüt faizi: Yasal sınırlar içinde kalıp kalmadığı
9. Sorumluluk sınırlandırmaları: Ağır kusur ve kasıt hallerinde sorumluluk sınırlandırılamaz
10. Yetki ve görev: Yetkili mahkeme ve zorunlu arabuluculuk şartları

ÖNEMLİ: Yukarıda sağlanan gerçek kanun maddelerini referans alarak analiz yap.
Risk bayraklarında mutlaka ilgili maddenin gerçek metninden alıntı yap.
"""

QUICK_SUMMARY_PROMPT = """
Aşağıdaki hukuki dokümanın kısa bir özetini Türkçe olarak çıkar (maksimum 3 cümle).
Türk Ticaret Kanunu ve Türk Borçlar Kanunu açısından kritik noktaları belirt:

{text}

Sadece özeti yaz, başka açıklama ekleme.
"""

RISK_ANALYSIS_PROMPT = """
Aşağıdaki hukuki dokümanda 6102 sayılı Türk Ticaret Kanunu (TTK) ve 6098 sayılı Türk Borçlar Kanunu (TBK)
hükümlerine göre kapsamlı risk analizi yap. Riskli ve sorunlu maddeleri belirle.

DOKÜMAN:
{text}

═══════════════════════════════════════════════════════════════
İLGİLİ KANUN MADDELERİ (TTK PDF'inden otomatik getirilmiştir)
═══════════════════════════════════════════════════════════════

{relevant_legal_articles}

JSON formatında yanıt ver:
{{
  "risk_flags": [
    {{
      "level": "critical|warning|info",
      "title": "risk başlığı",
      "description": "riskin TTK/TBK çerçevesinde detaylı açıklaması",
      "clause": "ilgili sözleşme maddesi",
      "legal_reference": "İlgili kanun maddeleri (örn: TTK m.18, TBK m.27, KVKK m.5)"
    }}
  ],
  "overall_risk_level": "low|medium|high|critical",
  "compliance_score": 0-100
}}

RİSK SEVİYESİ BELİRLEME KRİTERLERİ (TTK/TBK'ya göre):

CRITICAL (Kritik):
- Emredici kanun hükümlerine doğrudan aykırılık (TBK m.27 – kesin hükümsüzlük)
- KVKK ihlali riski taşıyan maddeler
- Yasadışı cezai şartlar veya sorumluluk sınırlandırmaları
- İş güvencesini ihlal eden hükümler

WARNING (Uyarı):
- Tek taraflı aşırı dezavantajlı maddeler (TBK m.28 – gabin)
- Orantısız cezai şartlar (hakim tarafından indirilebilir – TBK m.182)
- Belirsiz veya eksik hükümler (TTK m.18 – basiretli iş insanı ölçüsüne aykırı)
- Rekabet yasağının aşırı geniş kapsamı

INFO (Bilgi):
- İyileştirilebilecek hükümler
- Eksik ama zorunlu olmayan maddeler
- Tavsiye niteliğinde düzenlemeler

ÖNEMLİ: Yukarıda sağlanan gerçek kanun maddelerini referans alarak risk analizi yap.
"""

COMPARISON_PROMPT = """
Analiz edilen sözleşme ile referans sözleşme arasındaki temel farklılıkları
Türk Ticaret Kanunu (TTK) ve Türk Borçlar Kanunu (TBK) hükümleri çerçevesinde belirle.

ANALİZ EDİLEN SÖZLEŞME ÖZETİ:
{target_summary}

REFERANS SÖZLEŞME ÖZETİ:
{reference_summary}

Karşılaştırmayı aşağıdaki başlıklarda yap (Türkçe, 3-5 madde):
1. Yapısal farklılıklar
2. Risk açısından farklılıklar (TTK/TBK uyumu)
3. Eksik veya fazla maddeler
4. Hangisi hukuki açıdan daha güçlü/zayıf
"""
