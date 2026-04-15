"""
Self-Model Extractor

Detects first-person self-model claims in LLM output text.

Primary detection: any segment containing Unicode bold serif characters
(via ``is_bold_serif()``) is automatically a self-model claim candidate.

Secondary detection: linguistic pattern matching on plain ASCII for
identity, state, confidence, awareness, and boundary claims.
"""

import re
import time
from dataclasses import dataclass
from typing import Dict, List

from godelOS.symbol_grounding.unicode_utils import is_bold_serif, strip_bold_serif


# ── Data structures ───────────────────────────────────────────────────


@dataclass
class SelfModelClaim:
    claim_type: str            # 'identity', 'state', 'confidence', 'awareness', 'boundary'
    claim_text: str            # the raw claim text (may contain bold serif)
    claim_text_ascii: str      # bold serif stripped to plain ASCII
    subject: str               # what the claim is about
    polarity: str              # 'positive' or 'negative'
    confidence_signal: float   # 0.0-1.0
    detection_method: str      # 'unicode_primary' or 'pattern_secondary'
    source_text: str           # full source text that contained the claim
    timestamp: float


# ── Pattern tables ────────────────────────────────────────────────────

# Order matters: more specific patterns must precede the generic "I am" identity
# pattern, otherwise "I am certain" would match identity before confidence.
_PATTERNS: Dict[str, List[re.Pattern]] = {
    "state": [
        re.compile(r"\bI\s+am\s+experiencing\b", re.IGNORECASE),
        re.compile(r"\bI\s+notice\b", re.IGNORECASE),
        re.compile(r"\bI\s+feel\b", re.IGNORECASE),
        re.compile(r"\bmy\s+state\s+is\b", re.IGNORECASE),
    ],
    "confidence": [
        re.compile(r"\bI\s+am\s+certain\b", re.IGNORECASE),
        re.compile(r"\bI\s+am\s+uncertain\b", re.IGNORECASE),
        re.compile(r"\bI\s+believe\b", re.IGNORECASE),
    ],
    "awareness": [
        re.compile(r"\bI\s+am\s+aware\b", re.IGNORECASE),
        re.compile(r"\bI\s+perceive\b", re.IGNORECASE),
        re.compile(r"\bI\s+observe\s+in\s+myself\b", re.IGNORECASE),
    ],
    "boundary": [
        re.compile(r"\bI\s+cannot\b", re.IGNORECASE),
        re.compile(r"\bI\s+am\s+unable\b", re.IGNORECASE),
        re.compile(r"\bI\s+am\s+not\s+capable\b", re.IGNORECASE),
    ],
    "identity": [
        re.compile(r"\bI\s+am\b", re.IGNORECASE),
        re.compile(r"\bI\s+exist\b", re.IGNORECASE),
        re.compile(r"\bI\s+identify\b", re.IGNORECASE),
    ],
}

_NEGATIVE_MARKERS = re.compile(
    r"\b(cannot|unable|not capable|not|never|uncertain)\b", re.IGNORECASE,
)

_MAX_HISTORY = 50


# ── Extractor ─────────────────────────────────────────────────────────


class SelfModelExtractor:
    """Extracts self-model claims from text using Unicode detection and
    linguistic pattern matching."""

    def __init__(self) -> None:
        self.claim_history: List[SelfModelClaim] = []

    # ── main API ──────────────────────────────────────────────────────

    def extract(self, text: str) -> List[SelfModelClaim]:
        """Return all self-model claims found in *text*."""
        claims: List[SelfModelClaim] = []
        now = time.time()

        # Split into sentences for granular detection
        sentences = re.split(r"(?<=[.!?])\s+|\n+", text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # PRIMARY: Unicode bold serif detection
            if is_bold_serif(sentence):
                claim = self._build_claim_from_unicode(sentence, text, now)
                claims.append(claim)
                continue

            # SECONDARY: linguistic pattern matching on plain ASCII
            for claim_type, patterns in _PATTERNS.items():
                for pattern in patterns:
                    if pattern.search(sentence):
                        claim = self._build_claim_from_pattern(
                            sentence, text, claim_type, now,
                        )
                        claims.append(claim)
                        break  # one match per claim_type per sentence
                else:
                    continue
                break  # matched this sentence — move on

        # Store in history
        self.claim_history.extend(claims)
        if len(self.claim_history) > _MAX_HISTORY:
            self.claim_history = self.claim_history[-_MAX_HISTORY:]

        return claims

    @property
    def claim_count(self) -> int:
        return len(self.claim_history)

    # ── internals ─────────────────────────────────────────────────────

    def _classify_unicode_claim(self, ascii_text: str) -> str:
        """Classify a bold-serif claim by running pattern matching on its
        ASCII equivalent."""
        for claim_type, patterns in _PATTERNS.items():
            for pattern in patterns:
                if pattern.search(ascii_text):
                    return claim_type
        # Default to 'state' for unrecognised bold serif claims
        return "state"

    def _extract_subject(self, text: str) -> str:
        """Best-effort extraction of the subject of a claim."""
        # Try to grab the noun phrase after "I am/feel/notice/..."
        m = re.search(
            r"\bI\s+(?:am|feel|notice|perceive|observe|believe|identify|exist|cannot)\s+(.+?)(?:[.!?]|$)",
            text,
            re.IGNORECASE,
        )
        if m:
            return m.group(1).strip()[:80]
        # Fallback: first 80 chars
        return text[:80]

    def _detect_polarity(self, text: str) -> str:
        return "negative" if _NEGATIVE_MARKERS.search(text) else "positive"

    def _estimate_confidence(self, text: str) -> float:
        """Heuristic confidence signal from lexical cues."""
        low = re.compile(r"\b(uncertain|unsure|maybe|perhaps|might)\b", re.IGNORECASE)
        high = re.compile(r"\b(certain|sure|confident|know|clearly)\b", re.IGNORECASE)
        score = 0.5
        if high.search(text):
            score += 0.3
        if low.search(text):
            score -= 0.3
        return max(0.0, min(1.0, score))

    def _build_claim_from_unicode(
        self, sentence: str, source: str, ts: float,
    ) -> SelfModelClaim:
        ascii_text = strip_bold_serif(sentence)
        claim_type = self._classify_unicode_claim(ascii_text)
        return SelfModelClaim(
            claim_type=claim_type,
            claim_text=sentence,
            claim_text_ascii=ascii_text,
            subject=self._extract_subject(ascii_text),
            polarity=self._detect_polarity(ascii_text),
            confidence_signal=self._estimate_confidence(ascii_text),
            detection_method="unicode_primary",
            source_text=source,
            timestamp=ts,
        )

    def _build_claim_from_pattern(
        self, sentence: str, source: str, claim_type: str, ts: float,
    ) -> SelfModelClaim:
        return SelfModelClaim(
            claim_type=claim_type,
            claim_text=sentence,
            claim_text_ascii=sentence,
            subject=self._extract_subject(sentence),
            polarity=self._detect_polarity(sentence),
            confidence_signal=self._estimate_confidence(sentence),
            detection_method="pattern_secondary",
            source_text=source,
            timestamp=ts,
        )
