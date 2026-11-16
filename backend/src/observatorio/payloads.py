from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


def payload_fingerprint(feature: Mapping[str, Any]) -> str:
    """Return a stable SHA-256 fingerprint for a complete source Feature."""
    canonical = json.dumps(
        feature,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
