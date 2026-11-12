from __future__ import annotations

from observatorio.logging import redact_sensitive


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
