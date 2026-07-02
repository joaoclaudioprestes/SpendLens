import csv
from pathlib import Path


class CsvReporter:
    """Class responsible for writing the results to CSV files."""

    def write(self, results: dict, output_dir: Path) -> None:
        """Write the results to CSV files in the specified output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, rows in results.items():
            if not rows:
                continue
            with open(output_dir / f"{name}.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
