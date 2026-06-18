from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os

# ── Türkçe karakter desteği için TTF fontlarını kaydet ──
# Docker (Linux) ve Windows'ta çalışacak şekilde birden fazla font ailesi ve yol denenır.

_FONT_SEARCH_PATHS = [
    "/usr/share/fonts/truetype/dejavu",       # Debian/Ubuntu DejaVu
    "/usr/share/fonts/dejavu",                 # Fedora/RHEL
    "/usr/share/fonts/truetype",               # genel Linux
    os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts"),  # Windows
]

# Denenecek font aileleri (öncelik sırasıyla)
_FONT_FAMILIES = [
    {
        "name": "TRFont",
        "files": {
            "normal":     ["DejaVuSans.ttf", "arial.ttf", "NotoSans-Regular.ttf"],
            "bold":       ["DejaVuSans-Bold.ttf", "arialbd.ttf", "NotoSans-Bold.ttf"],
            "italic":     ["DejaVuSans-Oblique.ttf", "ariali.ttf", "NotoSans-Italic.ttf"],
            "boldItalic": ["DejaVuSans-BoldOblique.ttf", "arialbi.ttf", "NotoSans-BoldItalic.ttf"],
        },
    },
]


def _find_font(filename_candidates: list[str]) -> str | None:
    """Birden fazla aday dosya adı ve birden fazla dizinde font arar."""
    for directory in _FONT_SEARCH_PATHS:
        if not os.path.isdir(directory):
            continue
        for filename in filename_candidates:
            path = os.path.join(directory, filename)
            if os.path.isfile(path):
                return path
    return None


def _register_fonts() -> bool:
    """Türkçe destekli bir TTF font ailesini kaydet. Başarılıysa True döner."""
    from reportlab.pdfbase.pdfmetrics import registerFontFamily

    for family in _FONT_FAMILIES:
        base = family["name"]
        files = family["files"]

        paths = {}
        for variant, candidates in files.items():
            p = _find_font(candidates)
            if not p:
                break
            paths[variant] = p
        else:
            # Tüm 4 varyant bulundu — kaydet
            try:
                pdfmetrics.registerFont(TTFont(f"{base}",            paths["normal"]))
                pdfmetrics.registerFont(TTFont(f"{base}-Bold",       paths["bold"]))
                pdfmetrics.registerFont(TTFont(f"{base}-Italic",     paths["italic"]))
                pdfmetrics.registerFont(TTFont(f"{base}-BoldItalic", paths["boldItalic"]))
                registerFontFamily(
                    base,
                    normal=f"{base}",
                    bold=f"{base}-Bold",
                    italic=f"{base}-Italic",
                    boldItalic=f"{base}-BoldItalic",
                )
                return True
            except Exception:
                continue
    return False


_FONTS_OK = _register_fonts()
_FONT = "TRFont" if _FONTS_OK else "Helvetica"
_FONT_BOLD = "TRFont-Bold" if _FONTS_OK else "Helvetica-Bold"

PAGE_W = A4[0] - 4 * cm  # usable width (2cm margins each side)

RISK_HEX = {
    "critical": "#DC2626",
    "warning":  "#D97706",
    "info":     "#2563EB",
}
RISK_BG = {
    "critical": "#FEF2F2",
    "warning":  "#FFFBEB",
    "info":     "#EFF6FF",
}
LEVEL_LABELS = {
    "low":      "Düşük",
    "medium":   "Orta",
    "high":     "Yüksek",
    "critical": "Kritik",
}
RISK_BADGE_COLOR = {
    "low":      "#16A34A",
    "medium":   "#D97706",
    "high":     "#DC2626",
    "critical": "#7C3AED",
}


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "RPTitle", parent=base["Normal"],
            fontSize=20, fontName=_FONT_BOLD,
            textColor=colors.HexColor("#1E3A5F"),
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "RPSubtitle", parent=base["Normal"],
            fontSize=11, fontName=_FONT,
            textColor=colors.HexColor("#6B7280"),
            spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "RPH2", parent=base["Normal"],
            fontSize=12, fontName=_FONT_BOLD,
            textColor=colors.HexColor("#1E40AF"),
            spaceBefore=10, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "RPBody", parent=base["Normal"],
            fontSize=9.5, fontName=_FONT, leading=14, spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "RPSmall", parent=base["Normal"],
            fontSize=8.5, fontName=_FONT,
            textColor=colors.HexColor("#6B7280"), leading=12,
        ),
        "meta_key": ParagraphStyle(
            "RPMetaKey", parent=base["Normal"],
            fontSize=9, fontName=_FONT_BOLD,
            textColor=colors.HexColor("#374151"),
        ),
        "meta_val": ParagraphStyle(
            "RPMetaVal", parent=base["Normal"],
            fontSize=9, fontName=_FONT,
            textColor=colors.HexColor("#111827"),
        ),
        "rec": ParagraphStyle(
            "RPRec", parent=base["Normal"],
            fontSize=9.5, fontName=_FONT, leading=14, leftIndent=12, spaceAfter=4,
        ),
    }


def _hr(color="#E5E7EB", thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=colors.HexColor(color))


def _section(story, title, s):
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(title, s["h2"]))
    story.append(_hr())
    story.append(Spacer(1, 0.2 * cm))


def _table(data, col_widths, header_bg="#1E40AF"):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
        ("FONTNAME", (0, 1), (-1, -1), _FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


class ReportService:
    @staticmethod
    def generate_pdf(doc, analysis, user) -> bytes:
        buffer = io.BytesIO()
        pdf = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        s = _styles()
        story = []

        # ── Header ────────────────────────────────────────────────────────────
        story.append(Paragraph("LegalDoc Analyzer", s["title"]))
        story.append(Paragraph("Hukuki Doküman Analiz Raporu", s["subtitle"]))
        story.append(_hr("#1E40AF", thickness=2))
        story.append(Spacer(1, 0.4 * cm))

        # Meta table (2-column layout)
        risk_level = analysis.overall_risk_level or "low"
        risk_color = RISK_BADGE_COLOR.get(risk_level, "#374151")
        score_str = f"{analysis.compliance_score:.0f}/100" if analysis.compliance_score is not None else "—"

        meta = [
            ["Doküman", doc.original_filename or "—"],
            ["Doküman Tipi", analysis.document_type or "—"],
            ["Oluşturan", user.full_name or "—"],
            ["Tarih", datetime.now().strftime("%d.%m.%Y %H:%M")],
            ["Risk Seviyesi", f'<font color="{risk_color}"><b>{LEVEL_LABELS.get(risk_level, risk_level.capitalize())}</b></font>'],
            ["Uyumluluk Skoru", score_str],
        ]
        meta_data = [[Paragraph(k, s["meta_key"]), Paragraph(v, s["meta_val"])] for k, v in meta]
        mt = Table(meta_data, colWidths=[4 * cm, PAGE_W - 4 * cm])
        mt.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, -1), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
        ]))
        story.append(mt)

        # ── Summary ────────────────────────────────────────────────────────────
        if analysis.summary:
            _section(story, "Özet", s)
            story.append(Paragraph(analysis.summary, s["body"]))

        # ── Parties ────────────────────────────────────────────────────────────
        if analysis.parties:
            _section(story, "Taraflar", s)
            data = [["Rol", "İsim"]] + [[p.get("role", ""), p.get("name", "")] for p in analysis.parties]
            story.append(_table(data, [5 * cm, PAGE_W - 5 * cm]))

        # ── Key Dates ──────────────────────────────────────────────────────────
        if analysis.key_dates:
            _section(story, "Önemli Tarihler", s)
            data = [["Tarih", "Açıklama"]]
            for kd in analysis.key_dates:
                data.append([kd.get("date", ""), kd.get("label", "")])
            story.append(_table(data, [4 * cm, PAGE_W - 4 * cm]))

        # ── Risk Flags ─────────────────────────────────────────────────────────
        if analysis.risk_flags:
            _section(story, "Risk ve Uyarılar", s)
            for flag in analysis.risk_flags:
                level = flag.get("level", "info")
                hex_fg = RISK_HEX.get(level, "#374151")
                hex_bg = RISK_BG.get(level, "#F9FAFB")
                label = level.upper()
                title_text = flag.get("title", "")
                desc_text = flag.get("description", "")
                clause_text = flag.get("clause", "")

                legal_ref_text = flag.get("legal_reference", "")
                block = [
                    Paragraph(f'<font color="{hex_fg}"><b>[{label}]</b></font>  {title_text}', s["body"]),
                ]
                if desc_text:
                    block.append(Paragraph(desc_text, s["small"]))
                if clause_text:
                    block.append(Paragraph(f"<i>İlgili Madde: {clause_text}</i>", s["small"]))
                if legal_ref_text:
                    block.append(Paragraph(f"<i>Kanun Maddesi: {legal_ref_text}</i>", s["small"]))

                flag_data = [[block]]
                ft = Table(flag_data, colWidths=[PAGE_W])
                ft.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(hex_bg)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LINEAFTER", (0, 0), (0, -1), 3, colors.HexColor(hex_fg)),
                    ("ROUNDEDCORNERS", [4]),
                ]))
                story.append(KeepTogether([ft, Spacer(1, 0.15 * cm)]))
            story.append(Spacer(1, 0.1 * cm))

        # ── Clauses ────────────────────────────────────────────────────────────
        if analysis.clauses:
            _section(story, "Madde Analizi", s)
            for clause in analysis.clauses:
                title_text = clause.get("title", "")
                content_text = clause.get("content", "")
                clause_analysis = clause.get("analysis", "")
                clause_legal_ref = clause.get("legal_reference", "")

                block = []
                if title_text:
                    block.append(Paragraph(f"<b>{title_text}</b>", s["body"]))
                if content_text:
                    block.append(Paragraph(content_text, s["small"]))
                if clause_analysis:
                    block.append(Paragraph(f"<i>Analiz: {clause_analysis}</i>", s["small"]))
                if clause_legal_ref:
                    block.append(Paragraph(f"<i>Kanun Maddesi: {clause_legal_ref}</i>", s["small"]))

                cd = [[block]]
                ct = Table(cd, colWidths=[PAGE_W])
                ct.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
                ]))
                story.append(KeepTogether([ct, Spacer(1, 0.15 * cm)]))

        # ── Recommendations ────────────────────────────────────────────────────
        if analysis.recommendations:
            _section(story, "Öneriler", s)
            for i, rec in enumerate(analysis.recommendations, 1):
                story.append(Paragraph(f"<b>{i}.</b>  {rec}", s["rec"]))

        # ── Similar Contracts ─────────────────────────────────────────────────
        if analysis.similar_contracts:
            _section(story, "Benzer Sözleşmeler", s)
            data = [["Dosya Adı", "Benzerlik"]]
            for sc in analysis.similar_contracts:
                score = sc.get("score", 0)
                data.append([sc.get("filename", ""), f"{score:.1%}"])
            story.append(_table(data, [PAGE_W - 4 * cm, 4 * cm]))

        # ── Footer note ────────────────────────────────────────────────────────
        story.append(Spacer(1, 0.6 * cm))
        story.append(_hr())
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            f"Bu rapor LegalDoc Analyzer tarafından {datetime.now().strftime('%d.%m.%Y')} tarihinde oluşturulmuştur. "
            "Rapor bilgilendirme amaçlıdır; hukuki tavsiye yerine geçmez.",
            s["small"],
        ))

        pdf.build(story)
        return buffer.getvalue()
