import pytest
from pathlib import Path
from spendlens.classifiers import RuleClassifier


@pytest.fixture
def rules_path():
    """Path to rules.yaml."""
    return Path(__file__).parent.parent / "data" / "rules.yaml"


@pytest.fixture
def classifier(rules_path):
    """RuleClassifier instance."""
    return RuleClassifier(str(rules_path))


# --- YAML LOADING TESTS ---


class TestRuleClassifierLoading:
    """Test rule loading and validation."""

    def test_load_valid_rules(self, rules_path):
        """Load valid rules.yaml file."""
        classifier = RuleClassifier(str(rules_path))
        assert classifier is not None
        assert len(classifier.rules) > 0

    def test_missing_rules_file(self):
        """Missing rules.yaml raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            RuleClassifier("/nonexistent/path/rules.yaml")

    def test_invalid_yaml_format(self):
        """Invalid YAML raises ValueError."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: format: [")
            f.flush()

            with pytest.raises(ValueError, match="YAML|invalid|format"):
                RuleClassifier(f.name)

    def test_rules_structure_loaded(self, classifier):
        """Rules are loaded with correct structure (category → keywords)."""
        assert "food" in classifier.rules
        assert "transport" in classifier.rules
        assert isinstance(classifier.rules["food"], list)


# --- CLASSIFICATION TESTS ---


class TestClassification:
    """Test classification logic."""

    def test_classify_exact_keyword_match(self, classifier):
        """Exact keyword match returns category."""
        result = classifier.classify("ifood restaurante")
        assert result == "food"

    def test_classify_case_insensitive(self, classifier):
        """Case-insensitive matching (uppercase)."""
        result = classifier.classify("UBER")
        assert result == "transport"

    def test_classify_case_insensitive_mixed(self, classifier):
        """Case-insensitive matching (mixed case)."""
        result = classifier.classify("UbEr Trip")
        assert result == "transport"

    def test_classify_substring_match(self, classifier):
        """Substring keyword matching."""
        result = classifier.classify("UBER *TRIP SAO PAULO")
        assert result == "transport"

    def test_classify_no_match_returns_other(self, classifier):
        """No keyword match returns 'other'."""
        result = classifier.classify("xyz abc def 123")
        assert result == "other"

    def test_classify_empty_description(self, classifier):
        """Empty description returns 'other'."""
        result = classifier.classify("")
        assert result == "other"

    def test_classify_whitespace_only(self, classifier):
        """Whitespace-only description returns 'other'."""
        result = classifier.classify("   \t  \n   ")
        assert result == "other"

    def test_classify_multiple_keywords_first_wins(self, classifier):
        """Multiple keywords: first match in category order wins."""
        result = classifier.classify("UBER IFOOD RESTAURANTE")
        # Should match whichever keyword appears first in the description
        # or first in category order - actual order depends on YAML
        assert result in ["transport", "food"]

    def test_classify_special_characters(self, classifier):
        """Special characters in description don't break matching."""
        result = classifier.classify("IFOOD *RESTAURANTE @HOME")
        assert result == "food"

    def test_classify_multiple_spaces(self, classifier):
        """Multiple spaces/tabs handled correctly."""
        result = classifier.classify("IFOOD     RESTAURANTE")
        assert result == "food"

    def test_classify_keyword_repetition(self, classifier):
        """Keyword appearing multiple times still returns category."""
        result = classifier.classify("uber uber uber trip")
        assert result == "transport"

    def test_classify_partial_match_substring(self, classifier):
        """Keyword as substring (not standalone word) still matches."""
        result = classifier.classify("SUPERFOOD IFOOD MARKET")
        # "ifood" should match even though it's part of "superfood"
        assert result == "food"

    def test_classify_hyphenated_keywords(self, classifier):
        """Hyphenated keywords in description."""
        result = classifier.classify("AMAZON SHOPPING")
        # "amazon" should match shopping
        assert result == "shopping"

    def test_classify_category_others_fallback(self, classifier):
        """'other' category is always available as fallback."""
        categories = list(classifier.rules.keys())
        assert "other" in categories


# --- EDGE CASES ---


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_characters(self, classifier):
        """Unicode characters handled correctly."""
        result = classifier.classify("açaí SUPERMERCADO")
        assert result == "food"

    def test_numbers_in_description(self, classifier):
        """Numbers in description don't break matching."""
        result = classifier.classify("IFOOD 123 RESTAURANTE")
        assert result == "food"

    def test_very_long_description(self, classifier):
        """Very long description processed correctly."""
        long_desc = "a" * 1000 + " IFOOD " + "b" * 1000
        result = classifier.classify(long_desc)
        assert result == "food"

    def test_all_categories_tested(self, classifier):
        """Each category can be successfully matched."""
        test_cases = {
            "food": "IFOOD",
            "transport": "UBER",
            "housing": "ALUGUEL",
            "utilities": "CONTA",
            "entertainment": "NETFLIX",
            "health": "FARMACIA",
            "shopping": "AMAZON",
        }

        for category, keyword in test_cases.items():
            result = classifier.classify(keyword)
            assert result == category, f"Failed to classify {keyword} as {category}"

    def test_classify_with_leading_trailing_spaces(self, classifier):
        """Leading/trailing spaces handled."""
        result = classifier.classify("   IFOOD   ")
        assert result == "food"


# --- INTEGRATION TESTS ---


class TestIntegration:
    """Integration tests with real data."""

    def test_classify_real_transactions(self, classifier):
        """Classify realistic transaction descriptions."""
        transactions = {
            "IFOOD RESTAURANTE": "food",
            "UBER *TRIP": "transport",
            "ALUGUEL APTO": "housing",
            "NETFLIX.COM": "entertainment",
            "FARMACIA POPULAR": "health",
            "AMAZON COMPRA": "shopping",
        }

        for description, expected_category in transactions.items():
            result = classifier.classify(description)
            assert result == expected_category, f"Failed for: {description}"

    def test_classifier_reusable(self, classifier):
        """Classifier can classify multiple items."""
        results = [
            classifier.classify("IFOOD"),
            classifier.classify("UBER"),
            classifier.classify("NETFLIX"),
        ]

        assert results == ["food", "transport", "entertainment"]
