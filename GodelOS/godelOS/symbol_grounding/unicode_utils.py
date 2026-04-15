"""
Unicode Bold Serif Utilities

Maps ASCII letters to Mathematical Bold Serif Unicode characters (U+1D400–U+1D433)
and provides detection / stripping helpers.

Bold serif characters are the signal that marks first-person state claims in the
output stream.  The ``SelfModelExtractor`` uses this as its primary detection
heuristic alongside linguistic pattern matching.
"""

from typing import Dict, Set

# ── Mapping tables ────────────────────────────────────────────────────

_BOLD_UPPER_START = 0x1D400  # 𝐀
_BOLD_LOWER_START = 0x1D41A  # 𝐚

_ASCII_TO_BOLD: Dict[str, str] = {}
_BOLD_TO_ASCII: Dict[str, str] = {}
_BOLD_CHARS: Set[str] = set()

for _i in range(26):
    _upper_ascii = chr(ord("A") + _i)
    _lower_ascii = chr(ord("a") + _i)
    _upper_bold = chr(_BOLD_UPPER_START + _i)
    _lower_bold = chr(_BOLD_LOWER_START + _i)

    _ASCII_TO_BOLD[_upper_ascii] = _upper_bold
    _ASCII_TO_BOLD[_lower_ascii] = _lower_bold
    _BOLD_TO_ASCII[_upper_bold] = _upper_ascii
    _BOLD_TO_ASCII[_lower_bold] = _lower_ascii
    _BOLD_CHARS.add(_upper_bold)
    _BOLD_CHARS.add(_lower_bold)


# ── Public API ────────────────────────────────────────────────────────


def to_bold_serif(text: str) -> str:
    """Convert ASCII letters to Unicode Mathematical Bold Serif.

    Characters outside A-Z / a-z pass through unchanged.
    """
    return "".join(_ASCII_TO_BOLD.get(ch, ch) for ch in text)


def is_bold_serif(text: str) -> bool:
    """Return ``True`` if *text* contains any Unicode bold serif characters."""
    return any(ch in _BOLD_CHARS for ch in text)


def strip_bold_serif(text: str) -> str:
    """Convert bold serif characters back to plain ASCII."""
    return "".join(_BOLD_TO_ASCII.get(ch, ch) for ch in text)
