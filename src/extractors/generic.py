import csv
import chardet
from pathlib import Path
from .base_extractor import BaseExtractor, ExtractionResult


class GenericCSVExtractor(BaseExtractor):
    """Generic CSV extractor with robust error handling."""

    def __init__(self, accepted_fields: list[str], name: str = "CSV"):
        self.accepted_fields = accepted_fields
        self.name = name

    def extract(self, filepath: str) -> ExtractionResult:
        """
        Extract data from CSV file with error handling and deduplication.

        Handles:
        - File I/O errors (missing, permission, etc.)
        - Encoding detection (UTF-8, Latin-1, etc.)
        - CSV parsing errors
        - Missing/empty fields
        - Duplicate rows
        - UTF-8 BOM
        """
        rows = []
        errors = []
        seen_rows = set()

        try:
            file_path = Path(filepath)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {filepath}")
            if not file_path.is_file():
                raise FileNotFoundError(f"Path is not a file: {filepath}")

            # Detect encoding (UTF-8 with BOM, Latin-1, etc.)
            encoding = self._detect_encoding(file_path)

            with open(file_path, mode="r", encoding=encoding, newline="") as csvfile:
                try:
                    reader = csv.DictReader(csvfile)
                    if reader.fieldnames is None:
                        raise ValueError("CSV has no headers")

                    for idx, row in enumerate(reader, start=2):
                        try:
                            # Validate all required fields present
                            missing_fields = [
                                f for f in self.accepted_fields if f not in row
                            ]
                            if missing_fields:
                                errors.append(
                                    f"Line {idx}: Missing fields {missing_fields}"
                                )
                                continue

                            # Validate non-empty values
                            empty_fields = [
                                f
                                for f in self.accepted_fields
                                if not row[f] or not str(row[f]).strip()
                            ]
                            if empty_fields:
                                errors.append(
                                    f"Line {idx}: Empty fields {empty_fields}"
                                )
                                continue

                            # Extract only accepted fields and normalize
                            filtered_row = {
                                field: str(row[field]).strip()
                                for field in self.accepted_fields
                            }

                            # Deduplication: create hash of row
                            row_hash = tuple(sorted(filtered_row.items()))
                            if row_hash in seen_rows:
                                errors.append(f"Line {idx}: Duplicate row (skipped)")
                                continue

                            seen_rows.add(row_hash)
                            rows.append(filtered_row)

                        except Exception as e:
                            errors.append(f"Line {idx}: {str(e)}")
                            continue

                except csv.Error as e:
                    raise ValueError(f"CSV parsing error: {str(e)}")

        except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
            raise FileNotFoundError(f"Cannot read {filepath}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Extraction failed: {str(e)}")

        total_rows = len(rows) + len(
            [e for e in errors if "Duplicate" in e or "Empty" in e or "Missing" in e]
        )
        skipped_rows = len(errors)

        return ExtractionResult(
            rows=rows,
            total_rows=total_rows,
            skipped_rows=skipped_rows,
            errors=errors,
        )

    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding with fallback."""
        try:
            with open(file_path, "rb") as f:
                raw = f.read(10000)

            # Check for UTF-8 BOM
            if raw.startswith(b"\xef\xbb\xbf"):
                return "utf-8-sig"

            # Try chardet
            detected = chardet.detect(raw)
            if detected and detected.get("encoding"):
                return detected["encoding"]

            return "utf-8"

        except Exception:
            return "utf-8"  # fallback
