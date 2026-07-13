"""Week 1 Day 2 — validate free API keys / service reachability.

Reads .env (repo root), reports which keys are set, and live-pings the
providers that have credentials. Missing keys are reported as SKIP, not errors,
so this runs cleanly during incremental setup.

Usage:
    python data/scripts/check_keys.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]


def load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        print("!  no .env found at repo root (copy .env.example -> .env)")
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


OK, SKIP, FAIL = "OK  ", "SKIP", "FAIL"
results: list[tuple[str, str, str]] = []


def record(name: str, status: str, detail: str = "") -> None:
    results.append((name, status, detail))


def ping_gemini() -> None:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        return record("Gemini", SKIP, "no key")
    try:
        r = httpx.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            params={"key": key},
            timeout=15,
        )
        record("Gemini", OK if r.status_code == 200 else FAIL, f"HTTP {r.status_code}")
    except Exception as e:  # noqa: BLE001
        record("Gemini", FAIL, str(e)[:60])


def ping_groq() -> None:
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return record("Groq", SKIP, "no key")
    try:
        r = httpx.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=15,
        )
        record("Groq", OK if r.status_code == 200 else FAIL, f"HTTP {r.status_code}")
    except Exception as e:  # noqa: BLE001
        record("Groq", FAIL, str(e)[:60])


def ping_github() -> None:
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        return record("GitHub", SKIP, "no token")
    try:
        r = httpx.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        record("GitHub", OK if r.status_code == 200 else FAIL, f"HTTP {r.status_code}")
    except Exception as e:  # noqa: BLE001
        record("GitHub", FAIL, str(e)[:60])


def ping_qdrant() -> None:
    url = os.getenv("QDRANT_URL", "")
    if not url:
        return record("Qdrant", SKIP, "no url")
    try:
        r = httpx.get(f"{url.rstrip('/')}/collections", timeout=10)
        record("Qdrant", OK if r.status_code == 200 else FAIL, f"HTTP {r.status_code}")
    except Exception as e:  # noqa: BLE001
        record("Qdrant", FAIL, "unreachable (start docker compose?)")


def presence_only() -> None:
    for name, var in [
        ("Voyage", "VOYAGE_API_KEY"),
        ("OpenRouter", "OPENROUTER_API_KEY"),
        ("Anthropic", "ANTHROPIC_API_KEY"),
        ("Adzuna id", "ADZUNA_APP_ID"),
        ("LangSmith", "LANGSMITH_API_KEY"),
        ("Google OAuth", "OAUTH_GOOGLE_ID"),
        ("GitHub OAuth", "OAUTH_GITHUB_ID"),
    ]:
        record(name, OK if os.getenv(var) else SKIP, "set" if os.getenv(var) else "not set")


def main() -> int:
    load_env()
    ping_gemini()
    ping_groq()
    ping_github()
    ping_qdrant()
    presence_only()

    print("\n  KEY / SERVICE CHECK")
    print("  " + "-" * 44)
    for name, status, detail in results:
        print(f"  [{status}] {name:<16} {detail}")
    failures = [r for r in results if r[1] == FAIL]
    print("  " + "-" * 44)
    print(f"  {len(failures)} failure(s)\n")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
