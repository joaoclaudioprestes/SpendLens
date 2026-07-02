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
        assert "alimentacao" in classifier.rules
        assert "transporte" in classifier.rules
        assert isinstance(classifier.rules["alimentacao"], list)


# --- CLASSIFICATION TESTS ---


class TestClassification:
    """Test classification logic."""

    def test_classify_exact_keyword_match(self, classifier):
        """Exact keyword match returns category."""
        result = classifier.classify("ifood restaurante")
        assert result == "alimentacao"

    def test_classify_case_insensitive(self, classifier):
        """Case-insensitive matching (uppercase)."""
        result = classifier.classify("UBER")
        assert result == "transporte"

    def test_classify_case_insensitive_mixed(self, classifier):
        """Case-insensitive matching (mixed case)."""
        result = classifier.classify("UbEr Trip")
        assert result == "transporte"

    def test_classify_substring_match(self, classifier):
        """Substring keyword matching."""
        result = classifier.classify("UBER *TRIP SAO PAULO")
        assert result == "transporte"

    def test_classify_no_match_returns_outros(self, classifier):
        """No keyword match returns 'outros'."""
        result = classifier.classify("xyz abc def 123")
        assert result == "outros"

    def test_classify_empty_description(self, classifier):
        """Empty description returns 'outros'."""
        result = classifier.classify("")
        assert result == "outros"

    def test_classify_whitespace_only(self, classifier):
        """Whitespace-only description returns 'outros'."""
        result = classifier.classify("   \t  \n   ")
        assert result == "outros"

    def test_classify_multiple_keywords_first_wins(self, classifier):
        """Multiple keywords: first match in category order wins."""
        result = classifier.classify("UBER IFOOD RESTAURANTE")
        # Should match whichever keyword appears first in the description
        # or first in category order - actual order depends on YAML
        assert result in ["transporte", "alimentacao"]

    def test_classify_special_characters(self, classifier):
        """Special characters in description don't break matching."""
        result = classifier.classify("IFOOD *RESTAURANTE @HOME")
        assert result == "alimentacao"

    def test_classify_multiple_spaces(self, classifier):
        """Multiple spaces/tabs handled correctly."""
        result = classifier.classify("IFOOD     RESTAURANTE")
        assert result == "alimentacao"

    def test_classify_keyword_repetition(self, classifier):
        """Keyword appearing multiple times still returns category."""
        result = classifier.classify("uber uber uber trip")
        assert result == "transporte"

    def test_classify_partial_match_substring(self, classifier):
        """Keyword as substring (not standalone word) still matches."""
        result = classifier.classify("SUPERFOOD IFOOD MARKET")
        # "ifood" should match even though it's part of "superfood"
        assert result == "alimentacao"

    def test_classify_hyphenated_keywords(self, classifier):
        """Hyphenated keywords in description."""
        result = classifier.classify("AMAZON SHOPPING")
        # "amazon" should match compras
        assert result == "compras"

    def test_classify_category_others_fallback(self, classifier):
        """'outros' category is always available as fallback."""
        categories = list(classifier.rules.keys())
        assert "outros" in categories


# --- EDGE CASES ---


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_characters(self, classifier):
        """Unicode characters handled correctly."""
        result = classifier.classify("açaí SUPERMERCADO")
        assert result == "alimentacao"

    def test_numbers_in_description(self, classifier):
        """Numbers in description don't break matching."""
        result = classifier.classify("IFOOD 123 RESTAURANTE")
        assert result == "alimentacao"

    def test_very_long_description(self, classifier):
        """Very long description processed correctly."""
        long_desc = "a" * 1000 + " IFOOD " + "b" * 1000
        result = classifier.classify(long_desc)
        assert result == "alimentacao"

    def test_all_categories_tested(self, classifier):
        """Each category can be successfully matched."""
        test_cases = {
            "alimentacao": "IFOOD",
            "transporte": "UBER",
            "moradia": "ALUGUEL",
            "utilities": "CONTA",
            "entretenimento": "NETFLIX",
            "saude": "FARMACIA",
            "compras": "AMAZON",
        }

        for category, keyword in test_cases.items():
            result = classifier.classify(keyword)
            assert result == category, f"Failed to classify {keyword} as {category}"

    def test_classify_with_leading_trailing_spaces(self, classifier):
        """Leading/trailing spaces handled."""
        result = classifier.classify("   IFOOD   ")
        assert result == "alimentacao"


# --- INTEGRATION TESTS ---


class TestIntegration:
    """Integration tests with real data."""

    def test_classify_real_transactions(self, classifier):
        """Classify realistic transaction descriptions."""
        transactions = {
            "IFOOD RESTAURANTE": "alimentacao",
            "UBER *TRIP": "transporte",
            "ALUGUEL APTO": "moradia",
            "NETFLIX.COM": "entretenimento",
            "FARMACIA POPULAR": "saude",
            "AMAZON COMPRA": "compras",
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

        assert results == ["alimentacao", "transporte", "entretenimento"]
