"""Teste manual de comunicação com a API Gemini.

Execute explicitamente com:
    python -m scripts.test_gemini_connection
"""

import json
import re
import sys
from collections.abc import Mapping
from typing import Any

from src.agent.gemini_client import create_gemini_client
from src.config import settings

_SENSITIVE_FIELD_NAMES = {
    "key",
    "apikey",
    "geminiapikey",
    "authorization",
    "accesstoken",
    "refreshtoken",
    "credential",
    "credentials",
}


def _redact(value: Any) -> Any:
    """Remove credenciais conhecidas antes de exibir detalhes de erro."""
    if isinstance(value, Mapping):
        return {
            key: "[REDACTED]"
            if re.sub(r"[^a-z0-9]", "", str(key).lower()) in _SENSITIVE_FIELD_NAMES
            else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    if not isinstance(value, str):
        return value

    text = value
    api_key = settings.GEMINI_API_KEY
    if api_key:
        text = text.replace(api_key, "[REDACTED]")
    text = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED]", text)
    field_pattern = (
        r"(?i)([\"']?(?:gemini[_-]?api[_-]?key|x-goog-api-key|api[_-]?key|"
        r"authorization|access[_-]?token|refresh[_-]?token|credentials?|key)"
        r"[\"']?\s*[:=]\s*)(\"[^\"]*\"|'[^']*'|[^,\s}]+)"
    )
    return re.sub(field_pattern, r'\1"[REDACTED]"', text)


def _safe_text(value: Any, limit: int = 3000) -> str:
    try:
        text = json.dumps(_redact(value), ensure_ascii=False, default=str)
    except Exception:
        text = str(_redact(str(value)))
    if len(text) > limit:
        text = text[:limit] + "… [truncado]"
    return text


def _report_api_error(error: Exception) -> None:
    """Mostra detalhes úteis do SDK sem imprimir credenciais."""
    print(f"Tipo da exceção: {type(error).__name__}", file=sys.stderr)

    http_code = getattr(error, "code", None)
    response = getattr(error, "response", None)
    if http_code is None and response is not None:
        http_code = getattr(response, "status_code", None)
    print(f"Código HTTP: {http_code if http_code is not None else 'indisponível'}", file=sys.stderr)

    message = getattr(error, "message", None)
    if message:
        print(f"Mensagem do Google: {_safe_text(message)}", file=sys.stderr)

    status = getattr(error, "status", None)
    if status:
        print(f"Status do Google: {_safe_text(status)}", file=sys.stderr)

    details = getattr(error, "details", None)
    if details is not None:
        print(f"Detalhes do SDK: {_safe_text(details)}", file=sys.stderr)

    if response is not None:
        response_text = getattr(response, "text", None)
        if response_text:
            print(f"Corpo da resposta HTTP: {_safe_text(response_text)}", file=sys.stderr)

    if not message and details is None and response is None:
        print(f"Mensagem: {_safe_text(str(error))}", file=sys.stderr)


def main() -> int:
    try:
        client = create_gemini_client()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 2

    print(f"Modelo configurado: {settings.GEMINI_MODEL}", flush=True)
    try:
        interaction = client.interactions.create(
            model=settings.GEMINI_MODEL,
            input="Olá! Responda em português com uma breve saudação.",
        )
        response = interaction.output_text
        if not response:
            print("A API Gemini não retornou texto.", file=sys.stderr)
            return 1
        print(response)
        return 0
    except Exception as error:
        _report_api_error(error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

