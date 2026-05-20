"""Shared utilities for SentinelAI validation and demo scripts."""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import httpx

# ---------------------------------------------------------------------------
# Service URLs (Docker-aware defaults)
# ---------------------------------------------------------------------------
API_URL = os.getenv("SENTINEL_API_URL", os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000"))
FRONTEND_URL = os.getenv("SENTINEL_FRONTEND_URL", "http://localhost:3000")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinelai")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

DEMO_EMAIL = os.getenv("SENTINEL_DEMO_EMAIL", "admin@sentinelai.io")
DEMO_PASSWORD = os.getenv("SENTINEL_DEMO_PASSWORD", "demo")

DEFAULT_TIMEOUT = float(os.getenv("SENTINEL_HTTP_TIMEOUT", "30"))


# ---------------------------------------------------------------------------
# Terminal colours (cross-platform)
# ---------------------------------------------------------------------------
class Color:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def supports_color() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def c(text: str, *styles: str) -> str:
    if not supports_color():
        return text
    return "".join(styles) + text + Color.RESET


def ok(msg: str) -> str:
    return c(f"✓ {msg}", Color.GREEN)


def fail(msg: str) -> str:
    return c(f"✗ {msg}", Color.RED)


def warn(msg: str) -> str:
    return c(f"! {msg}", Color.YELLOW)


def info(msg: str) -> str:
    return c(f"→ {msg}", Color.CYAN)


# ---------------------------------------------------------------------------
# Check result tracking
# ---------------------------------------------------------------------------
@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str = ""
    duration_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckReport:
    results: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def success(self) -> bool:
        return self.failed == 0

    def add(self, result: CheckResult) -> None:
        self.results.append(result)

    def run(self, name: str, fn: Callable[[], Any], required: bool = True) -> CheckResult:
        start = time.perf_counter()
        try:
            detail = fn()
            msg = detail if isinstance(detail, str) else "ok"
            result = CheckResult(name, True, msg, (time.perf_counter() - start) * 1000)
        except Exception as exc:
            result = CheckResult(
                name, False, str(exc), (time.perf_counter() - start) * 1000
            )
        self.add(result)
        status = ok(name) if result.passed else fail(name)
        suffix = f" ({result.duration_ms:.0f}ms)" if result.duration_ms else ""
        detail = f": {result.message}" if result.message and result.message != "ok" else ""
        print(f"  {status}{suffix}{detail}")
        return result

    def summary(self) -> int:
        print()
        print(c("=" * 60, Color.BOLD))
        total = len(self.results)
        if self.success:
            print(ok(f"All {total} checks passed"))
        else:
            print(fail(f"{self.failed}/{total} checks failed"))
            for r in self.results:
                if not r.passed:
                    print(f"  {fail(r.name)}: {r.message}")
        print(c("=" * 60, Color.BOLD))
        return 0 if self.success else 1


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
def get_client(timeout: float = DEFAULT_TIMEOUT) -> httpx.Client:
    return httpx.Client(timeout=timeout, follow_redirects=True)


def login(client: httpx.Client | None = None, base_url: str = API_URL) -> str:
    owns = client is None
    client = client or get_client()
    try:
        resp = client.post(
            f"{base_url}/api/v1/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        if not token:
            raise RuntimeError("Empty access token returned")
        return token
    finally:
        if owns:
            client.close()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def check_http(name: str, url: str, expected_status: int = 200) -> None:
    with get_client(timeout=10) as client:
        resp = client.get(url)
        if resp.status_code != expected_status:
            raise RuntimeError(f"HTTP {resp.status_code} from {url}")
        return None


def retry_call(
    fn: Callable[[], Any],
    retries: int = 3,
    delay: float = 2.0,
    label: str = "operation",
) -> Any:
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(delay)
    raise RuntimeError(f"{label} failed after {retries} attempts: {last_exc}")
