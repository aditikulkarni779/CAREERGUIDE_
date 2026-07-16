"""Verification agent — gate answers so claims are grounded in retrieved context."""
from __future__ import annotations

import json
import re

from app.agents.llm.port import LLMClient, Message
from app.rag.types import Chunk

_SYSTEM = (
    "You are a strict fact-checker. Given an ANSWER and the SOURCES it should be "
    "based on, decide whether the answer's claims are supported by the sources. "
    'Respond ONLY with compact JSON: {"supported": true|false, "reason": "..."}.'
)


class Verifier:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def verify(self, answer: str, chunks: list[Chunk]) -> tuple[bool, str]:
        if not answer.strip():
            return False, "empty answer"
        if not chunks:
            # nothing to ground against; allow but flag
            return True, "no sources retrieved"
        sources = "\n\n".join(f"[{i}] {c.text}" for i, c in enumerate(chunks, 1))
        user = f"SOURCES:\n{sources}\n\nANSWER:\n{answer}"
        try:
            raw = self._llm.complete(_SYSTEM, [Message("user", user)], tier="fast", max_tokens=120)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            data = json.loads(match.group() if match else raw)
            return bool(data.get("supported", True)), str(data.get("reason", ""))
        except Exception:  # noqa: BLE001 — fail open (don't block on verifier errors)
            return True, "verifier unavailable"
