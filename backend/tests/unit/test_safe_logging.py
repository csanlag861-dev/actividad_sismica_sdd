from __future__ import annotations

from observatorio.logging import redact_sensitive
from observatorio.producer.source import safe_source_url


def test_database_credentials_and_tokens_are_redacted() -> None:
    message = (
        "could not connect to postgresql+asyncpg://reader:very-secret@postgres:5432/db; "
        "token=abc123 Authorization: Bearer bearer-secret"
    )
    redacted = redact_sensitive(message)
    assert "very-secret" not in redacted
    assert "abc123" not in redacted
    assert "bearer-secret" not in redacted
    assert "[REDACTED]" in redacted


def test_source_urls_remove_credentials_and_sensitive_query_parameters() -> None:
    safe_url = safe_source_url(
        "https://user:password@example.test/feed?format=geojson&api_key=hidden&token=secret"
    )

    assert safe_url == "https://example.test/feed?format=geojson"
    assert "password" not in safe_url
    assert "hidden" not in safe_url
    assert "secret" not in safe_url
