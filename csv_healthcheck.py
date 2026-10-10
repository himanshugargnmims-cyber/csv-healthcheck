"""Small, dependency-free CSV quality report."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path


class CSVProfileError(ValueError):
    """Raised when a CSV cannot be profiled safely and consistently."""


def profile_csv(path: str | Path) -> dict:
    """Profile one UTF-8 CSV. Only empty or whitespace-only cells are missing."""
    source = Path(path)
    try:
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, strict=True)
            headers = next(reader, None)
            if not headers:
                raise CSVProfileError("CSV must have a header row")
            if any(not header.strip() for header in headers):
                raise CSVProfileError("CSV headers cannot be blank")
            if len(set(headers)) != len(headers):
                raise CSVProfileError("CSV headers must be unique")

            missing = {header: 0 for header in headers}
            numbers: dict[str, list[float]] = {header: [] for header in headers}
            numeric = {header: True for header in headers}
            seen: set[tuple[str, ...]] = set()
            duplicate_rows = 0
            rows = 0

            for row in reader:
                if len(row) != len(headers):
                    raise CSVProfileError(
                        f"record {rows + 1} has {len(row)} cells; expected {len(headers)}"
                    )
                rows += 1
                key = tuple(row)
                if key in seen:
                    duplicate_rows += 1
                else:
                    seen.add(key)
                for header, value in zip(headers, row):
                    if not value.strip():
                        missing[header] += 1
                        continue
                    if numeric[header]:
                        try:
                            parsed = float(value.strip())
                        except ValueError:
                            numeric[header] = False
                        else:
                            if math.isfinite(parsed):
                                numbers[header].append(parsed)
                            else:
                                numeric[header] = False
    except (OSError, UnicodeError, csv.Error) as exc:
        raise CSVProfileError(str(exc)) from exc

    numeric_stats = {}
    for header in headers:
        values = numbers[header]
        if numeric[header] and values:
            numeric_stats[header] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": round(math.fsum(value / len(values) for value in values), 4),
            }
    return {
        "file": source.name,
        "rows": rows,
        "columns": len(headers),
        "duplicate_rows": duplicate_rows,
        "missing_by_column": missing,
        "numeric_columns": numeric_stats,
    }


def render_text(report: dict) -> str:
    lines = [
        f"File: {report['file']}",
        f"Rows: {report['rows']}  Columns: {report['columns']}  Duplicate rows: {report['duplicate_rows']}",
        "Missing values (blank cells):",
    ]
    lines.extend(f"  {name}: {count}" for name, count in report["missing_by_column"].items())
    lines.append("Numeric columns (all nonblank values must be numeric):")
    if not report["numeric_columns"]:
        lines.append("  None")
    else:
        for name, stats in report["numeric_columns"].items():
            lines.append(
                f"  {name}: count={stats['count']} min={stats['min']:g} "
                f"max={stats['max']:g} mean={stats['mean']:g}"
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Profile a UTF-8 CSV file")
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args(argv)
    try:
        report = profile_csv(args.csv_file)
    except CSVProfileError as exc:
        print(f"csv-healthcheck: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2) if args.json else render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
