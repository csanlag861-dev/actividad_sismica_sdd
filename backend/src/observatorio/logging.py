from __future__ import annotations

import logging
import re

_SECRET_PATTERNS = (
    (
        re.compile(
            r"([a-z][a-z0-9+.-]*://)([^:/@\s]+):([^@/\s]+)@",
            re.IGNORECASE,
        ),
        r"\1[REDACTED]@",
    ),
    (
        re.compile(r"(password|passwd|pwd|token|secret|dsn|uri)\s*[:=]\s*['\"]?[^\s,'\"]+", re.IGNORECASE),
        r"\1=[REDACTED]",
    ),
    (re.compile(r"(Authorization:\s*Bearer\s+)[^\s]+", re.IGNORECASE), r"\1[REDACTED]"),
)


def redact_sensitive(value: str) -> str:
    redacted = value
    for pattern, replacement in _SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    key: redact_sensitive(value) if isinstance(value, str) else value
                    for key, value in record.args.items()
                }
            else:
                record.args = tuple(
                    redact_sensitive(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        record.msg = redact_sensitive(record.getMessage())
        record.args = ()
        return True


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        handler.addFilter(RedactingFilter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
