import re

from config import settings

_PATTERNS = [
    ("OPENAI_KEY", r"\bsk-[A-Za-z0-9\-_]{20,}"),
    ("GEMINI_KEY", r"\bAIza[A-Za-z0-9\-_]{35,}"),
    ("AWS_KEY", r"\bAKIA[A-Z0-9]{14,16}\b"),
    ("AWS_SECRET", r"(?i)aws.{0,20}secret.{0,10}['\"]?[A-Za-z0-9/+]{40}['\"]?"),
    ("GITHUB_TOKEN", r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b"),
    ("STRIPE_KEY", r"\b(sk|pk)_(test|live)_[A-Za-z0-9]{24,}\b"),
    ("SLACK_TOKEN", r"\bxox[baprs]-[A-Za-z0-9\-]{10,}"),
    ("JWT", r"\beyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_.+/=]+"),
    ("SECRET", r"(?i)(password|passwd|token|api[_\s]?key|secret)\s*[=:]\s*\S+"),
    ("EMAIL", r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    ("CARD", r"\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}\b|\b\d{16}\b"),
    ("PHONE", r"(\+?38)?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"),
]

_ENTROPY_PLUGINS = None


def _get_entropy_plugins():
    global _ENTROPY_PLUGINS
    if _ENTROPY_PLUGINS is not None:
        return _ENTROPY_PLUGINS
    try:
        from detect_secrets.plugins.high_entropy_strings import (
            Base64HighEntropyString,
            HexHighEntropyString,
        )

        _ENTROPY_PLUGINS = [
            Base64HighEntropyString(settings.PRIVACY_ENTROPY_BASE64),
            HexHighEntropyString(settings.PRIVACY_ENTROPY_HEX),
        ]
    except ImportError:
        _ENTROPY_PLUGINS = []
    return _ENTROPY_PLUGINS


def _entropy_scan(text: str) -> list[str]:
    plugins = _get_entropy_plugins()
    if not plugins:
        return []

    from detect_secrets.core.scan import scan_line
    from detect_secrets.settings import transient_settings

    plugin_configs = [
        {"name": "Base64HighEntropyString", "limit": settings.PRIVACY_ENTROPY_BASE64},
        {"name": "HexHighEntropyString", "limit": settings.PRIVACY_ENTROPY_HEX},
    ]

    found = []
    with transient_settings({"plugins_used": plugin_configs}):
        for secret in scan_line(text):
            val = secret.secret_value
            if val and len(val) >= settings.PRIVACY_MIN_SECRET_LEN:
                found.append(val)
    return found


class PrivacyGuard:
    def mask(self, text: str) -> tuple[str, dict[str, str]]:
        mapping: dict[str, str] = {}
        counters: dict[str, int] = {}

        for label, pattern in _PATTERNS:
            for match in re.finditer(pattern, text):
                original = match.group()
                if original in mapping.values():
                    continue
                if "[" in original and "]" in original:
                    continue
                counters[label] = counters.get(label, 0) + 1
                placeholder = f"[{label}_{counters[label]}]"
                mapping[placeholder] = original
                text = text.replace(original, placeholder)

        entropy_secrets = _entropy_scan(text)
        for val in entropy_secrets:
            if val in mapping.values():
                continue
            already_masked = any(val in ph for ph in mapping)
            if already_masked:
                continue
            counters["ENTROPY"] = counters.get("ENTROPY", 0) + 1
            placeholder = f"[ENTROPY_{counters['ENTROPY']}]"
            mapping[placeholder] = val
            text = text.replace(val, placeholder, 1)

        return text, mapping

    def unmask(self, text: str, mapping: dict[str, str]) -> str:
        for placeholder, original in mapping.items():
            text = text.replace(placeholder, original)
        return text
