from datetime import datetime
from .base_transformer import BaseTransformer, Transaction


class ItauTransformer(BaseTransformer):
    """Transform Itau CSV rows to canonical Transaction schema."""

    def transform(self, raw_row: dict) -> Transaction:
        """
        Transform Itau row: (data_lancamento, historico, valor, tipo) → Transaction.

        Tipo mapping:
        - "D" (Debit) → "expense"
        - "C" (Credit) → "income"

        Date format: DD/MM/YYYY

        Args:
            raw_row: Dict with keys: data_lancamento, historico, valor, tipo

        Returns:
            Transaction with canonical schema

        Raises:
            ValueError: If validation fails
        """
        # Validate required fields
        required_fields = ["data_lancamento", "historico", "valor", "tipo"]
        missing = [f for f in required_fields if f not in raw_row]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Validate non-empty values
        date_str = raw_row["data_lancamento"]
        description = raw_row["historico"]
        value_str = raw_row["valor"]
        type_raw = raw_row["tipo"]

        if not date_str or not isinstance(date_str, str):
            raise ValueError("Field 'data_lancamento' is empty or invalid")

        if not description or not isinstance(description, str):
            raise ValueError("Field 'historico' is empty or invalid")

        if not value_str:
            raise ValueError("Field 'valor' is empty or invalid")

        if not type_raw or not isinstance(type_raw, str):
            raise ValueError("Field 'tipo' is empty or invalid")

        # Parse date (expected format: DD/MM/YYYY)
        try:
            date = datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
        except ValueError as e:
            raise ValueError(
                f"Invalid date format in 'data_lancamento' field (expected DD/MM/YYYY): {date_str}"
            ) from e

        # Parse value
        try:
            value = float(value_str)
        except ValueError as e:
            raise ValueError(f"Invalid value (must be numeric): {value_str}") from e

        # Reject zero values
        if value == 0:
            raise ValueError("Value cannot be zero")

        # Map type: C/D → income/expense
        type_upper = type_raw.strip().upper()
        if type_upper == "C":
            type_ = "income"
        elif type_upper == "D":
            type_ = "expense"
        else:
            raise ValueError(f"Invalid type (must be 'C' or 'D'): {type_raw}")

        # Make value always positive
        value = abs(value)

        # Normalize description
        description = description.strip()

        return Transaction(
            date=date,
            description=description,
            value=value,
            type=type_,
            source="itau",
        )
