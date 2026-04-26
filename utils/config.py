"""
Configuration module for the voting voucher generator.
Version: 1.1.0

Single source of truth for all constants, file paths, and barcode variants.
"""

__version__ = "1.1.0"

from dataclasses import dataclass
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXCEL_FILENAME = DATA_DIR / "test_data.xlsx"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ── Data models ────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class BarcodeVariation:
    """Describes one barcode-type/output-file combination.

    Attributes:
        type: Barcode format identifier passed to ReportLab (Code128, Code39,
            DataMatrix, QR).
        filename: Absolute path of the PDF to be written.
    """

    type: str
    filename: Path


# ── Constants ──────────────────────────────────────────────────────────────
BARCODE_VARIATIONS: list[BarcodeVariation] = [
    BarcodeVariation(type="Code128",    filename=DATA_DIR / "vouchers_code128.pdf"),
    # BarcodeVariation(type="Code39",     filename=DATA_DIR / "vouchers_code39.pdf"),
    # BarcodeVariation(type="DataMatrix", filename=DATA_DIR / "vouchers_datamatrix.pdf"),
    BarcodeVariation(type="QR",         filename=DATA_DIR / "vouchers_qr.pdf"),
]

NUM_SHAREHOLDERS: int = 5
NUM_VOTES: int = 3   # Must be ≤ 9 — see barcode format constraint in CLAUDE.md
MAX_SHARES: int = 100  # Encoded as 3 digits; values above 999 break the barcode format


# ── Helpers ────────────────────────────────────────────────────────────────
def get_safe_path(base_path: Path) -> Path:
    """Return a writable path, avoiding locked files on Windows.

    If *base_path* is locked (PermissionError), appends ``_1``, ``_2``, …
    until a writable path is found.

    Args:
        base_path: Desired output path.

    Returns:
        The first path that can be opened for writing.

    Raises:
        OSError: If an unexpected OS error occurs beyond a simple PermissionError.
    """
    if not base_path.exists():
        return base_path

    try:
        with open(base_path, "ab"):
            pass
        return base_path
    except PermissionError:
        pass

    suffix = 1
    while True:
        candidate = base_path.with_stem(f"{base_path.stem}_{suffix}")
        if not candidate.exists():
            return candidate
        try:
            with open(candidate, "ab"):
                pass
            return candidate
        except PermissionError:
            suffix += 1
