from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """Result of extraction with metadata."""

    rows: list[dict]
    total_rows: int
    skipped_rows: int
    errors: list[str]


class BaseExtractor(ABC):
    """Base class for all extractors."""

    accepted_fields: list[str] = []

    @abstractmethod
    def extract(self, filepath: str) -> ExtractionResult:
        """
        Extracts data from source file.

        Args:
            filepath: Path to the file to extract data from.

        Returns:
            ExtractionResult with rows, stats, and errors.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file is unreadable or format invalid.
        """
        pass
