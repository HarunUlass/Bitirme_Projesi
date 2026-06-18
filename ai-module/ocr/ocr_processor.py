import os
from ocr.pdf_extractor import PDFExtractor
from ocr.docx_extractor import DOCXExtractor
from ocr.image_extractor import ImageExtractor, SUPPORTED_EXTENSIONS as IMAGE_EXTS

PDF_EXTS  = {"pdf"}
DOCX_EXTS = {"docx", "doc"}
IMG_EXTS  = {e.lstrip(".") for e in IMAGE_EXTS}


class OCRProcessor:
    def __init__(self):
        self.pdf   = PDFExtractor()
        self.docx  = DOCXExtractor()
        self.image = ImageExtractor()

    def extract(self, file_path: str, ext: str) -> str:
        ext = ext.lower().lstrip(".")

        if ext in PDF_EXTS:
            text = self.pdf.extract(file_path)
            if not text.strip():
                text = self._ocr_pdf_fallback(file_path)
            return text

        if ext in DOCX_EXTS:
            return self.docx.extract(file_path)

        if ext in IMG_EXTS:
            return self.image.extract(file_path)

        raise ValueError(f"Desteklenmeyen dosya tipi: {ext}")

    def _ocr_pdf_fallback(self, file_path: str) -> str:
        """Taranmış PDF için pytesseract ile OCR."""
        try:
            import pytesseract
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, dpi=300)
            texts = [pytesseract.image_to_string(img, lang="tur+eng") for img in images]
            return "\n\n".join(texts)
        except ImportError:
            return ""
        except Exception as e:
            return f"OCR hatası: {e}"
