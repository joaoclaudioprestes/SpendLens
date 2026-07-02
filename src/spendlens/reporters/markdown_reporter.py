from pathlib import Path


class MarkdownReporter:
    """Class responsible for writing the results to Markdown files."""

    def write(self, results: dict, output_path: Path) -> None:
        """Write the results to a Markdown file at the specified output path."""
        lines = ["# SpendLens Report", ""]
        for name, rows in results.items():
            lines.append(f"## {name.replace('_', ' ').title()}")
            lines.append("")
            if not rows:
                lines.append("_No data._")
                lines.append("")
                continue
            headers = list(rows[0].keys())
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join("---" for _ in headers) + " |")
            for row in rows:
                lines.append("| " + " | ".join(str(v) for v in row.values()) + " |")
            lines.append("")
        output_path.write_text("\n".join(lines))
