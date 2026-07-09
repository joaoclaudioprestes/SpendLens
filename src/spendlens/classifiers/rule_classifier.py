from pathlib import Path
import yaml


class RuleClassifier:
    """Classify transactions by rule-based keyword matching."""

    def __init__(self, rules_path: str = "data/rules.yaml"):
        """
        Initialize classifier with rules from YAML file.

        Args:
            rules_path: Path to rules.yaml file

        Raises:
            FileNotFoundError: If rules file doesn't exist
            ValueError: If YAML is invalid
        """
        self.rules_path = Path(rules_path)

        if not self.rules_path.exists():
            raise FileNotFoundError(f"Rules file not found: {rules_path}")

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                rules_data = yaml.safe_load(f)

            if not isinstance(rules_data, dict):
                raise ValueError("Rules YAML must be a dictionary")

            self.rules = {}
            for category, data in rules_data.items():
                if isinstance(data, dict) and "keywords" in data:
                    self.rules[category] = [
                        str(k).lower().strip() for k in data["keywords"]
                    ]
                else:
                    self.rules[category] = []

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}") from e

    def classify(self, description: str) -> str:
        """
        Classify description by keyword matching.

        Matching is case-insensitive and substring-based.
        Returns first matching category or "other" (default).

        Args:
            description: Transaction description string

        Returns:
            Category name (string)
        """
        if not description or not description.strip():
            return "other"

        description_lower = description.lower()

        for category, keywords in self.rules.items():
            for keyword in keywords:
                if keyword in description_lower:
                    return category

        return "other"
