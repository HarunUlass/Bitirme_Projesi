import pdfplumber
import io


class PDFExtractor:
    def extract(self, file_path: str) -> str:
        text_parts = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            raise RuntimeError(f"PDF okuma hatası: {e}")
        return "\n\n".join(text_parts)

    def extract_pages(self, file_path: str) -> list[str]:
        pages = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages.append(text)
        return pages
