"""
Lightweight API-key authentication for the Weather App backend.
Clients pass their key in the Authorization header:
  Authorization: Bearer <api_key>
or as a query parameter:
  ?api_key=<api_key>

For development the key defaults to "dev" — change via AUTH_API_KEY env var.
"""

import os
import secrets
from fastapi import Security
from fastapi.security import APIKeyHeader, APIKeyQuery

_VALID_KEY = os.getenv("AUTH_API_KEY", "dev")

_header_scheme = APIKeyHeader(name="Authorization", auto_error=False)
_query_scheme = APIKeyQuery(name="api_key", auto_error=False)


def _extract(raw: str | None) -> str | None:
    """Strip 'Bearer ' prefix if present."""
    if not raw:
        return None
    return raw.removeprefix("Bearer ").strip()


# Optional dependency — does NOT raise, just returns None if unauthenticated.
async def optional_api_key(
    header_key: str | None = Security(_header_scheme),
    query_key: str | None = Security(_query_scheme),
) -> str | None:
    key = _extract(header_key) or query_key
    if key and secrets.compare_digest(key, _VALID_KEY):
        return key
    return None
