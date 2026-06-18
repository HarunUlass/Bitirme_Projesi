import google.generativeai as genai
from typing import Optional
import os


class GeminiClient:
    _instance: Optional["GeminiClient"] = None

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY ortam değişkeni ayarlanmamış")
        genai.configure(api_key=api_key)
        self.pro_model = genai.GenerativeModel(
            os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                max_output_tokens=8192,
            ),
        )
        self.flash_model = genai.GenerativeModel(
            os.getenv("GEMINI_FLASH_MODEL", "gemini-3.1-flash-lite"),
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=8192,
            ),
        )
        self.embedding_model = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")

    @classmethod
    def get(cls) -> "GeminiClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def generate(self, prompt: str, use_flash: bool = False) -> str:
        model = self.flash_model if use_flash else self.pro_model
        response = model.generate_content(prompt)
        return response.text

    def embed(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        result = genai.embed_content(
            model=self.embedding_model,
            content=text[:8000],
            task_type=task_type,
        )
        return result["embedding"]

    def embed_batch(self, texts: list[str], task_type: str = "retrieval_document") -> list[list[float]]:
        """Birden fazla metni tek API çağrısıyla göm (batch embedding)."""
        truncated = [t[:8000] for t in texts]
        result = genai.embed_content(
            model=self.embedding_model,
            content=truncated,
            task_type=task_type,
        )
        return result["embedding"]

    def embed_query(self, text: str) -> list[float]:
        return self.embed(text, task_type="retrieval_query")
