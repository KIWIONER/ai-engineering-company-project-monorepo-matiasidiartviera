"""
services/api/rate_limiter.py
Rate limiting por usuario y control de tamaño máximo de entrada para endpoints de IA.
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, status

MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "4000"))
DEFAULT_LLM_RATE_LIMIT = int(os.getenv("LLM_RATE_LIMIT_PER_MINUTE", "20"))
DEFAULT_WINDOW_SECONDS = int(os.getenv("LLM_RATE_WINDOW_SECONDS", "60"))


class SlidingWindowRateLimiter:
    """Limitador de tasa en memoria por identificador de usuario."""

    def __init__(
        self,
        max_requests: int = DEFAULT_LLM_RATE_LIMIT,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Límite de solicitudes de IA alcanzado. Intenta de nuevo más tarde.",
                )
            bucket.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


llm_rate_limiter = SlidingWindowRateLimiter()


def enforce_llm_guards(user: dict, text: str, *, limiter: SlidingWindowRateLimiter = llm_rate_limiter) -> None:
    """Aplica límite de tamaño de entrada y rate limiting por usuario autenticado."""
    if len(text or "") > MAX_PROMPT_CHARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La consulta excede el máximo permitido de {MAX_PROMPT_CHARS} caracteres.",
        )
    user_key = str(user.get("id") or user.get("email") or "anonymous")
    limiter.check(user_key)