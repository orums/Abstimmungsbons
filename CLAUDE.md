# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This project uses `uv` for dependency management.

```bash
# Install dependencies
uv sync

# Run the full pipeline (generate test data + all 4 PDF variants)
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

## Architecture

The pipeline has three stages that run in sequence from `main.py`:

1. **`generate_test_data.py`** — Creates synthetic shareholder data (`data/test_data.xlsx`) with columns `sh_nr`, `name`, `Vorname`, `anz_akt`. Uses an exponential distribution for share counts so most shareholders have few shares.

2. **`generate_vouchers.py`** — Reads the Excel file and renders a PDF of voting vouchers using ReportLab. The layout is fixed: A4 page, 3 columns (JA / NEIN / ENTH), up to 7 voting rounds per page. Each shareholder gets their own page(s). The barcode value encodes all information needed for scanning: `[VoteNr][Type][ShareholderNr].[ShareCount]` (e.g. `2N012.045` = round 2, NEIN, shareholder 12, 45 shares).

3. **`utils/config.py`** — Single source of truth for all constants (`NUM_VOTES`, `NUM_SHAREHOLDERS`, `MAX_SHARES`, file paths, barcode variants). Also provides `get_safe_path()` which handles locked PDFs on Windows by appending `_1`, `_2`, etc.

`main.py` calls `create_vouchers()` four times — once per barcode type (Code128, Code39, DataMatrix, QR) — producing four separate PDFs in `data/`.

### Key constraint
`NUM_VOTES` must be ≤ 9 due to the fixed 7-vouchers-per-page layout and single-digit vote number in the barcode format. Exceeding this requires changing both the page-break logic in `generate_vouchers.py` and the barcode encoding scheme.

# Python Best Practices für Claude

1. **Type Hinting**: Nutze konsequent Typ-Annotationen für alle Funktionsargumente und Rückgabewerte.
2. **Plan-First**: Erstelle vor der Implementierung immer erst einen technischen Plan in `<plan>` Tags.
3. **Modulare Struktur**: Halte Funktionen kurz und trenne Logik strikt nach dem Single-Responsibility-Prinzip.
4. **Strukturierte Dokumentation**: Schreibe für jedes Modul und jede Funktion Docstrings im Google-Stil.
5. **Datenmodellierung**: Bevorzuge `Pydantic`-Modelle oder `dataclasses` gegenüber einfachen Dictionaries.
<!-- 6. **Testgetriebene Entwicklung**: Erstelle für jedes neue Feature sofort passende `pytest`-Testfälle. -->
7. **Präzises Error Handling**: Verwende spezifische Exceptions anstelle von generischen `try-except`-Blöcken.
8. **PEP 8 Konformität**: Halte dich strikt an Python-Coding-Standards und nutze Tools wie `Ruff` zur Formatierung.
9. **Abhängigkeitsmanagement**: Dokumentiere alle neuen Bibliotheken für `uv` und trage diese in pyproject.toml ein
10. **Kontext-Hygiene**: Referenziere nur die Dateien, die für die aktuelle Aufgabe zwingend notwendig sind.

