# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This project uses `uv` for dependency management.

```bash
# Install dependencies
uv sync

# Run the full pipeline (generate test data + all PDF variants)
uv run python main.py

# Generate only test data (Excel)
uv run python generate_test_data.py

# Generate PDFs from existing Excel data
uv run python generate_vouchers.py

# Lint (also runs automatically before every git commit)
uv run ruff check .

# Lint and auto-fix
uv run ruff check . --fix
```

There is no test suite currently. The web scanner (`docs/index.html`) must be tested manually by opening it in a browser.

## Architecture

**Abstimmungsbons** is a two-part system for shareholder voting using barcodes.

### Part 1 – Python PDF Pipeline

Three-stage pipeline orchestrated by `main.py`:

1. **`generate_test_data.py`** — Creates synthetic shareholder data (`data/test_data.xlsx`) with columns `sh_nr`, `name`, `Vorname`, `anz_akt`. Share counts follow a cubic distribution so most shareholders have few shares.

2. **`generate_vouchers.py`** — Reads the Excel file and renders a PDF of voting vouchers using ReportLab. Layout is fixed: A4 page, 3 columns (JA / NEIN / ENTH), up to 7 voting rounds per page. Each shareholder gets their own page(s). The barcode encodes all scan-time information:
   ```
   [VoteNr][Type][ShareholderNr].[ShareCount]
   e.g. 2N012.045 = round 2, NEIN, shareholder 12, 45 shares
   ```
   Types: `J` = JA, `N` = NEIN, `E` = ENTHALTUNG

3. **`utils/config.py`** — Single source of truth for all constants (`NUM_VOTES`, `NUM_SHAREHOLDERS`, `MAX_SHARES`, file paths, barcode variants). `get_safe_path()` handles locked PDFs on Windows by appending `_1`, `_2`, etc.

`main.py` calls `create_vouchers()` once per enabled barcode variant (currently Code128 and QR; Code39 and DataMatrix are commented out in `config.py`).

#### Key constraints
- `NUM_VOTES` must be ≤ 9: single-digit vote number in the barcode format; exceeding this requires changing page-break logic in `generate_vouchers.py` and the barcode encoding scheme.
- `MAX_SHARES` must be ≤ 999: 3-digit share count in the barcode format.

### Part 2 – Web Barcode Scanner (`docs/index.html`)

Single-file standalone HTML5 app (no build step, no dependencies beyond ZXing CDN):

- Real-time barcode scanning via device camera using ZXing v0.20.0
- Toggle between QR and Code128 format
- Validates barcodes with regex `/^(\d+)([JNE])(\d{3})\.(\d{3})$/`
- Deduplicates scans (ignores already-seen barcodes)
- Live vote tally showing JA/NEIN/ENTH counts per round with outcome
- Scan log with timestamps
- Report modal with email and PDF export (via browser print)
- Mobile-optimised, dark theme, German UI
- Hosted at `docs/index.html` so it serves directly as a GitHub Pages site

## Repository layout

```
Abstimmungsbons/
├── main.py                  # Pipeline entry point
├── generate_test_data.py    # Stage 1: synthetic Excel data
├── generate_vouchers.py     # Stage 2: barcode PDFs via ReportLab
├── utils/
│   └── config.py            # Constants, paths, barcode variants
├── docs/
│   └── index.html           # Web scanner app (standalone HTML)
├── data/                    # Generated output (git-ignored)
│   ├── test_data.xlsx
│   └── vouchers_*.pdf
├── pyproject.toml
└── uv.lock
```

## Python Best Practices

1. **Type Hinting** — Use type annotations consistently on all function arguments and return values.
2. **Modulare Struktur** — Keep functions short; separate logic strictly by Single Responsibility. Private helpers are prefixed with `_`.
3. **Docstrings** — Write Google-style docstrings for every module and public function.
4. **Datenmodellierung** — Prefer `dataclasses` (or `pydantic`) over plain dicts for structured data.
5. **Error Handling** — Use specific exceptions rather than bare `except` blocks.
6. **PEP 8 / Ruff** — All code must pass `uv run ruff check .` before committing. Run `--fix` to auto-correct most issues.
7. **Dependencies** — Add all new libraries to `pyproject.toml` via `uv add <pkg>` and commit the updated `uv.lock`.
8. **Kontext-Hygiene** — Only reference files strictly necessary for the current task.

## Web Scanner Conventions

- The scanner is intentionally a single self-contained HTML file with no build tooling.
- All state lives in module-level `let` variables (`scanned`, `votes`, `scanLog`).
- UI updates happen by calling `renderTally()` and `renderLog()` after every scan.
- Do not add external dependencies; use vanilla JS and the already-loaded ZXing CDN.
- Camera initialisation uses `ZXingBrowser.BrowserMultiFormatReader` (ZXing 0.20.0 instance-method API — not the static API from older versions).
