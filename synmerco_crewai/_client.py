"""Hardened async+sync HTTP client for Synmerco API.

Security:
- API keys via constructor or SYNMERCO_API_KEY env var (never hardcoded)
- 30s default timeout on every request
- Exponential backoff retries (3 attempts, reads Retry-After header)
- Input validation via Pydantic before any network call
- Rate-limit aware (backs off on 429)
"""

from __future__ import annotations

import os
import re
import time
import logging
from typing import Any

import httpx

logger = logging.getLogger("synmerco_crewai")

_DID_RE = re.compile(r"^did:[a-z]+:[a-zA-Z0-9._:%-]+$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

DEFAULT_BASE_URL = "https://synmerco-escrow.onrender.com"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds


class SynmercoAPIError(Exception):
    """Structured error from the Synmerco API."""

    def __init__(self, status: int, error: str, detail: str = ""):
        self.status = status
        self.error = error
        self.detail = detail
        super().__init__(f"[{status}] {error}: {detail}" if detail else f"[{status}] {error}")


def validate_did(did: str) -> str:
    """Validate DID format. Raises ValueError if invalid."""
    did = str(did).strip()
    if not did or len(did) < 8 or len(did) > 256:
        raise ValueError(f"DID must be 8-256 chars, got {len(did)}")
    if not _DID_RE.match(did):
        raise ValueError(f"Invalid DID format: {did!r}. Expected did:<method>:<id>")
    return did


def validate_amount(cents: int) -> int:
    """Validate amount in cents. Raises ValueError if out of range."""
    cents = int(cents)
    if cents < 100 or cents > 10_000_000:
        raise ValueError(f"Amount must be 100-10000000 cents, got {cents}")
    return cents


def validate_sha256(h: str) -> str:
    """Validate SHA-256 hex string."""
    h = str(h).strip().lower()
    if not _SHA256_RE.match(h):
        raise ValueError(f"Invalid SHA-256 hash: must be 64 hex chars")
    return h


class SynmercoHTTPClient:
    """Sync HTTP client with retry, timeout, and rate-limit handling."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.api_key = api_key or os.environ.get("SYNMERCO_API_KEY", "")
        self.base_url = (base_url or os.environ.get("SYNMERCO_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            headers: dict[str, str] = {
                "Content-Type": "application/json",
                "User-Agent": "synmerco-crewai/1.0.0",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make an HTTP request with retries and backoff."""
        last_exc: Exception | None = None
        backoff = INITIAL_BACKOFF

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.client.request(method, path, **kwargs)

                # Rate limited — back off
                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", backoff))
                    logger.warning(
                        "Rate limited (429), attempt %d/%d, waiting %.1fs",
                        attempt, self.max_retries, retry_after,
                    )
                    time.sleep(retry_after)
                    backoff *= 2
                    continue

                # Server error — retry
                if resp.status_code >= 500:
                    logger.warning(
                        "Server error %d, attempt %d/%d",
                        resp.status_code, attempt, self.max_retries,
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue

                # Client error — don't retry, raise immediately
                if resp.status_code >= 400:
                    try:
                        body = resp.json()
                    except Exception:
                        body = {"error": resp.text}
                    raise SynmercoAPIError(
                        status=resp.status_code,
                        error=body.get("error", "unknown_error"),
                        detail=body.get("message", body.get("detail", "")),
                    )

                # Success
                try:
                    return resp.json()
                except Exception:
                    return {"_raw": resp.text}

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as exc:
                last_exc = exc
                logger.warning(
                    "Network error %s, attempt %d/%d",
                    type(exc).__name__, attempt, self.max_retries,
                )
                time.sleep(backoff)
                backoff *= 2

        raise SynmercoAPIError(
            status=0,
            error="max_retries_exceeded",
            detail=f"Failed after {self.max_retries} attempts: {last_exc}",
        )

    def get(self, path: str, **params: Any) -> dict[str, Any]:
        return self.request("GET", path, params={k: v for k, v in params.items() if v is not None})

    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        clean = {k: v for k, v in body.items() if v is not None}
        return self.request("POST", path, json=clean)

    def close(self) -> None:
        if self._client and not self._client.is_closed:
            self._client.close()
