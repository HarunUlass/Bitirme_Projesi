import os
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}


class ImageExtractor:
    def extract(self, file_path: str) -> str:
        img = Image.open(file_path)
        img = self._preprocess(img)
        text = pytesseract.image_to_string(img, lang="tur+eng", config="--psm 3")
        return text.strip()

    def _preprocess(self, img: Image.Image) -> Image.Image:
        # Convert to RGB if needed (handles RGBA/P modes)
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")

        # Upscale small images for better OCR accuracy
        w, h = img.size
        if w < 1000 or h < 1000:
            scale = max(1000 / w, 1000 / h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # Convert to grayscale and sharpen
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = img.filter(ImageFilter.SHARPEN)
        return img
