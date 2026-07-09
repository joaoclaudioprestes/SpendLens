from datetime import datetime
from .base_transformer import BaseTransformer, Transaction


class NubankTransformer(BaseTransformer):
    """Transform Nubank CSV rows to canonical Transaction schema."""

    def transform(self, raw_row: dict) -> Transaction:
        """
        Transform Nubank row: (Data, Descrição, Valor) → Transaction.

        Tipo is inferred from Valor sign:
        - Negative valor → "expense"
        - Positive valor → "income"

        Args:
            raw_row: Dict with keys: Data, Descrição, Valor

        Returns:
            Transaction with canonical schema

        Raises:
            ValueError: If validation fails
        """
        # Validate required fields
        required_fields = ["Data", "Descrição", "Valor"]
        missing = [f for f in required_fields if f not in raw_row]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Validate non-empty values
        date_str = raw_row["Data"]
        description = raw_row["Descrição"]
        value_str = raw_row["Valor"]

        if not date_str or not isinstance(date_str, str):
            raise ValueError("Field 'Data' is empty or invalid")

        if not description or not isinstance(description, str):
            raise ValueError("Field 'Descrição' is empty or invalid")

        if not value_str:
            raise ValueError("Field 'Valor' is empty or invalid")

        # Parse date (expected format: YYYY-MM-DD)
        try:
            date = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(f"Invalid date format in 'Data' field: {date_str}") from e

        # Parse value
        try:
            value = float(value_str)
        except ValueError as e:
            raise ValueError(f"Invalid value (must be numeric): {value_str}") from e

        # Reject zero values
        if value == 0:
            raise ValueError("Value cannot be zero")

        # Infer type from sign and make value positive
        if value < 0:
            type_ = "expense"
            value = abs(value)
        else:
            type_ = "income"

        # Normalize description
        description = description.strip()

        return Transaction(
            date=date,
            description=description,
            value=value,
            type=type_,
            source="nubank",
        )
