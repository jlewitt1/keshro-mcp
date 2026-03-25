from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_url: str
    api_token: str
    timeout_seconds: float = 30.0


def load_settings() -> Settings:
    api_url = (os.getenv("KESHRO_API_URL") or "http://localhost:8000/api/v1").rstrip("/")
    api_token = (os.getenv("KESHRO_API_TOKEN") or "").strip()
    if not api_token:
        raise RuntimeError("KESHRO_API_TOKEN is required")
    timeout_raw = (os.getenv("KESHRO_API_TIMEOUT") or "30").strip()
    try:
        timeout = float(timeout_raw)
    except ValueError as exc:
        raise RuntimeError("KESHRO_API_TIMEOUT must be numeric") from exc
    return Settings(api_url=api_url, api_token=api_token, timeout_seconds=timeout)
