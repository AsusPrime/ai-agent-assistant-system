import re

_PATTERNS = [
    ("EMAIL",  r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    ("PHONE",  r"(\+?38)?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"),
    ("CARD",   r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    ("SECRET", r"(?i)(password|passwd|token|api[_\s]?key|secret)\s*[=:]\s*\S+"),
]


class PrivacyGuard:
    def mask(self, text: str) -> tuple[str, dict[str, str]]:
        """Returns (masked_text, {placeholder: original}) mapping."""
        mapping: dict[str, str] = {}
        counters: dict[str, int] = {}
        for label, pattern in _PATTERNS:
            for match in re.finditer(pattern, text):
                original = match.group()
                if original in mapping.values():
                    continue
                counters[label] = counters.get(label, 0) + 1
                placeholder = f"[{label}_{counters[label]}]"
                mapping[placeholder] = original
                text = text.replace(original, placeholder, 1)
        return text, mapping
