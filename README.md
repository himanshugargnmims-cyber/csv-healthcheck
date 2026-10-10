# csv-healthcheck

A tiny, dependency-free CSV quality check you can run before trusting a spreadsheet export or data handoff.

## What it does

Reports row and column counts, blank cells by column, repeated data rows, and min/max/mean for columns whose nonblank values are all finite numbers. Results can be read in a terminal or consumed as JSON.

## Quick start

Requires Python 3.10 or newer. No packages to install.

```bash
python3 csv_healthcheck.py examples/people.csv
python3 csv_healthcheck.py examples/people.csv --json
python3 -m unittest discover -s tests -v
```

Example output:

```text
File: people.csv
Rows: 4  Columns: 3  Duplicate rows: 1
Missing values (blank cells):
  name: 0
  score: 1
  team: 0
Numeric columns (all nonblank values must be numeric):
  score: count=3 min=10 max=20 mean=16.6667
```

## Rules and limits

- The first record must contain unique, nonblank column names. Each subsequent record must have the same number of cells.
- A missing value is an empty or whitespace-only cell. Text such as `NA` or `null` is kept as text.
- Duplicate rows compare every cell exactly, including whitespace and case.
- A column gets numeric statistics only when every nonblank cell parses as a finite number. Mean is rounded to four decimals.
- Input must be UTF-8 (a UTF-8 BOM is accepted). This tool does not infer types, validate business rules, or repair data.
- Duplicate detection stores seen rows in memory, so use a database or streaming tool for very large files.

## License

MIT. See [LICENSE](LICENSE).
