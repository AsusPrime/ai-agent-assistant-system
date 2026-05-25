"""
Tests for PrivacyGuard — regex patterns + entropy-based detection.
Run: cd src && python -m pytest ../tests/test_privacy.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.privacy import PrivacyGuard

guard = PrivacyGuard()


# ==================== REGEX PATTERNS ====================


class TestOpenAIKey:
    def test_detects_sk_key(self):
        text = "key: sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
        masked, mapping = guard.mask(text)
        assert "[OPENAI_KEY_1]" in masked
        assert "sk-proj" not in masked

    def test_detects_short_sk_key(self):
        text = "sk-abcdefghijklmnopqrstuvwxyz"
        masked, mapping = guard.mask(text)
        assert "[OPENAI_KEY_1]" in masked


class TestGeminiKey:
    def test_detects_aiza_key(self):
        text = "my key AIzaSyB-abcdefghijk1234567890LMNOP_qrst"
        masked, mapping = guard.mask(text)
        assert "[GEMINI_KEY_1]" in masked
        assert "AIza" not in masked

    def test_short_aiza_not_gemini(self):
        text = "AIzaShort"
        masked, mapping = guard.mask(text)
        has_gemini = any("GEMINI" in k for k in mapping)
        assert not has_gemini


class TestAWSKey:
    def test_detects_akia(self):
        text = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
        masked, mapping = guard.mask(text)
        assert "[AWS_KEY_1]" in masked
        assert "AKIA" not in masked

    def test_detects_aws_secret(self):
        text = "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        masked, mapping = guard.mask(text)
        assert "wJalr" not in masked


class TestGitHubToken:
    def test_detects_ghp(self):
        text = "ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890"
        masked, mapping = guard.mask(text)
        assert "[GITHUB_TOKEN_1]" in masked
        assert "ghp_" not in masked

    def test_detects_gho(self):
        text = "gho_aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890"
        masked, mapping = guard.mask(text)
        assert "[GITHUB_TOKEN_1]" in masked


class TestStripeKey:
    def test_detects_sk_live(self):
        text = "sk_live_abcdefghijklmnopqrstuvwx"
        masked, mapping = guard.mask(text)
        assert "[STRIPE_KEY_1]" in masked

    def test_detects_pk_test(self):
        text = "pk_test_abcdefghijklmnopqrstuvwx"
        masked, mapping = guard.mask(text)
        assert "[STRIPE_KEY_1]" in masked


class TestSlackToken:
    def test_detects_xoxb(self):
        text = "my slack xoxb-123456789-abcdefgh here"
        masked, mapping = guard.mask(text)
        assert "[SLACK_TOKEN_1]" in masked
        assert "xoxb" not in masked

    def test_detects_xoxp(self):
        text = "xoxp-9876543210-abcdefghij"
        masked, mapping = guard.mask(text)
        assert "[SLACK_TOKEN_1]" in masked


class TestJWT:
    def test_detects_jwt(self):
        text = "bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        masked, mapping = guard.mask(text)
        assert "[JWT_1]" in masked
        assert "eyJ" not in masked


class TestGenericSecret:
    def test_password_equals(self):
        text = "password = MyP@ss123"
        masked, mapping = guard.mask(text)
        assert "[SECRET_1]" in masked
        assert "MyP@ss" not in masked

    def test_api_key_colon(self):
        text = "api_key: some_value_here"
        masked, mapping = guard.mask(text)
        assert "[SECRET_1]" in masked

    def test_token_equals(self):
        text = "token=abc123xyz"
        masked, mapping = guard.mask(text)
        assert "[SECRET_1]" in masked


class TestEmail:
    def test_simple_email(self):
        text = "contact john@example.com please"
        masked, mapping = guard.mask(text)
        assert "[EMAIL_1]" in masked
        assert "john@" not in masked

    def test_complex_email(self):
        text = "user.name+tag@sub.domain.co.uk"
        masked, mapping = guard.mask(text)
        assert "[EMAIL_1]" in masked

    def test_multiple_emails(self):
        text = "a@b.com and c@d.org"
        masked, mapping = guard.mask(text)
        assert "[EMAIL_1]" in masked
        assert "[EMAIL_2]" in masked


class TestPhone:
    def test_ua_full(self):
        text = "тел: +380501234567"
        masked, mapping = guard.mask(text)
        assert "[PHONE_1]" in masked

    def test_ua_with_brackets(self):
        text = "телефон (050) 123-45-67"
        masked, mapping = guard.mask(text)
        assert "[PHONE_1]" in masked

    def test_ua_short(self):
        text = "0501234567"
        masked, mapping = guard.mask(text)
        assert "[PHONE_1]" in masked


class TestCard:
    def test_card_with_spaces(self):
        text = "картка 4111 2222 3333 4444"
        masked, mapping = guard.mask(text)
        assert "[CARD_1]" in masked
        assert "4111" not in masked

    def test_card_with_dashes(self):
        text = "5500-0000-0000-0004"
        masked, mapping = guard.mask(text)
        assert "[CARD_1]" in masked

    def test_card_no_separator(self):
        text = "card: 4111222233334444"
        masked, mapping = guard.mask(text)
        assert "[CARD_1]" in masked
        assert "4111" not in masked


# ==================== ENTROPY DETECTION ====================


class TestEntropyDetection:
    def test_high_entropy_string(self):
        text = "config: aR4nD0mStr1ngW1thH1ghEntr0pyValu3sHere99"
        masked, mapping = guard.mask(text)
        has_entropy = any("ENTROPY" in k for k in mapping)
        assert has_entropy, f"Expected entropy detection, got: {mapping}"

    def test_normal_text_not_flagged(self):
        text = "просто звичайний текст українською мовою"
        masked, mapping = guard.mask(text)
        assert masked == text
        assert len(mapping) == 0

    def test_short_string_not_flagged(self):
        text = "key: abc"
        masked, mapping = guard.mask(text)
        has_entropy = any("ENTROPY" in k for k in mapping)
        assert not has_entropy

    def test_common_words_not_flagged(self):
        text = "the quick brown fox jumps over the lazy dog"
        masked, mapping = guard.mask(text)
        assert len(mapping) == 0


# ==================== UNMASK ====================


class TestUnmask:
    def test_unmask_restores_original(self):
        original = "ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890"
        masked, mapping = guard.mask(original)
        restored = guard.unmask(masked, mapping)
        assert restored == original

    def test_unmask_multiple(self):
        original = "email john@test.com and AIzaSyB-abcdefghijk1234567890LMNOP_qrst"
        masked, mapping = guard.mask(original)
        restored = guard.unmask(masked, mapping)
        assert restored == original

    def test_unmask_empty_mapping(self):
        text = "no secrets here"
        result = guard.unmask(text, {})
        assert result == text


# ==================== EDGE CASES ====================


class TestEdgeCases:
    def test_empty_string(self):
        masked, mapping = guard.mask("")
        assert masked == ""
        assert len(mapping) == 0

    def test_duplicate_values_masked_once(self):
        text = "john@test.com and john@test.com"
        masked, mapping = guard.mask(text)
        assert masked.count("[EMAIL_1]") == 2
        assert "john@test.com" not in masked
        assert len([k for k in mapping if "EMAIL" in k]) == 1

    def test_mixed_secrets(self):
        text = "email: user@mail.com, key: ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890, card: 4111 2222 3333 4444"
        masked, mapping = guard.mask(text)
        assert "[EMAIL_1]" in masked
        assert "[GITHUB_TOKEN_1]" in masked
        assert "[CARD_1]" in masked
        assert "user@" not in masked
        assert "ghp_" not in masked
        assert "4111" not in masked

    def test_no_false_positive_on_urls(self):
        text = "visit https://example.com/path?q=hello"
        masked, mapping = guard.mask(text)
        has_secret = any(
            k for k in mapping if "SECRET" in k or "OPENAI" in k or "GEMINI" in k
        )
        assert not has_secret

    def test_preserves_surrounding_text(self):
        text = "before john@test.com after"
        masked, mapping = guard.mask(text)
        assert masked.startswith("before ")
        assert masked.endswith(" after")


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
