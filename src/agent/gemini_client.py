"""Cliente oficial do Google Gemini."""

from google import genai

from src.config import settings


def create_gemini_client() -> genai.Client:
    """Cria o cliente Gemini usando a chave configurada no ambiente."""
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY não configurada. Copie .env.example para .env e "
            "preencha a chave, ou defina a variável no ambiente."
        )
    return genai.Client(api_key=settings.GEMINI_API_KEY)
