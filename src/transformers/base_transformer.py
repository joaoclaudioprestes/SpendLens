from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class Transaction:
    """Canonical transaction schema."""

    date: date
    description: str
    value: float
    type: str
    source: str


class BaseTransformer(ABC):
    """Base class for all transaction transformers."""

    @abstractmethod
    def transform(self, raw_row: dict) -> Transaction:
        """
        Transform raw row from bank CSV to canonical Transaction.

        Args:
            raw_row: Raw dictionary from extractor (bank-specific fields)

        Returns:
            Transaction: Normalized transaction with canonical schema

        Raises:
            ValueError: If validation fails (missing fields, invalid values, etc.)
            TypeError: If type conversion fails
        """
        pass
