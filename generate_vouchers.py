"""
Voucher generation module for the voting voucher pipeline.
Version: 1.1.0

Reads shareholder data from an Excel file and renders a PDF of voting
vouchers using ReportLab.

Layout:
    - Page size: A4
    - Grid: 3 columns (JA, NEIN, ENTH) × 7 rows (voting rounds per page)
    - Each shareholder starts on a fresh page.

Barcode format:
    ``[VoteNr][Type][ShareholderNr].[ShareCount]``

    - VoteNr:       Voting round number (1–9)
    - Type:         J = JA, N = NEIN, E = ENTH
    - ShareholderNr: 3-digit zero-padded shareholder ID
    - ShareCount:    3-digit zero-padded share count

    Example: ``2N012.045`` → round 2, NEIN, shareholder 12, 45 shares.

Barcode types:
    - Code128:    High-density linear; supports full ASCII; compact.
    - Code39:     Linear (Extended39); less dense than Code128.
    - QR:         2-D matrix; high capacity; omnidirectional scan.
    - DataMatrix: 2-D matrix; extremely compact; ideal for small items.
"""

__version__ = "1.1.0"

import os
from pathlib import Path
from typing import Literal

import pandas as pd
from reportlab.graphics.barcode import code128, code39
from reportlab.graphics.barcode.widgets import BarcodeECC200DataMatrix
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from utils.config import NUM_VOTES

BarcodeType = Literal["Code128", "Code39", "DataMatrix", "QR"]

# ── Layout constants ───────────────────────────────────────────────────────
_MARGIN_X: float = 10 * mm
_MARGIN_Y: float = 15 * mm
_VOUCHERS_PER_PAGE: int = 7
_VOTE_LABELS: dict[str, str] = {"J": "JA", "N": "NEIN", "E": "ENTH"}
_VOTE_TYPES: list[str] = ["J", "N", "E"]


# ── Font registration ──────────────────────────────────────────────────────
def _register_fonts() -> str:
    """Register a monospaced font for the human-readable barcode text.

    Tries Consolas (Windows); falls back to the built-in Courier-Bold.

    Returns:
        The name of the registered (or fallback) font.
    """
    font_path = "C:/Windows/Fonts/consola.ttf"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont("Consolas", font_path))
            return "Consolas"
        except Exception:
            pass
    return "Courier-Bold"


# ── Barcode factory ────────────────────────────────────────────────────────
def _make_barcode(value: str, bc_type: BarcodeType) -> tuple[object, float, float]:
    """Create a ReportLab barcode object for the given type and value.

    Args:
        value:   The data string to encode.
        bc_type: One of ``Code128``, ``Code39``, ``DataMatrix``, ``QR``.

    Returns:
        A tuple of ``(barcode_object, width_pts, height_pts)``.

    Raises:
        ValueError: If *bc_type* is not a recognised barcode format.
    """
    if bc_type == "Code128":
        bc = code128.Code128(value, barHeight=15 * mm, barWidth=0.35 * mm)
        return bc, bc.width, 15 * mm

    if bc_type == "Code39":
        bc = code39.Extended39(value, barHeight=15 * mm, barWidth=0.25 * mm)
        return bc, bc.width, 15 * mm

    if bc_type == "DataMatrix":
        size = 3.75 * mm
        bc = BarcodeECC200DataMatrix(value=value)
        bc.width = size
        bc.height = size
        bc.x = 0
        bc.y = 0
        d = Drawing(size, size)
        d.add(bc)
        return d, size, size

    if bc_type == "QR":
        from reportlab.graphics.barcode.qr import QrCodeWidget

        qr = QrCodeWidget(value)
        size = 18 * mm
        bounds = qr.getBounds()
        qr_w, qr_h = bounds[2] - bounds[0], bounds[3] - bounds[1]
        d = Drawing(size, size, transform=[size / qr_w, 0, 0, size / qr_h, 0, 0])
        d.add(qr)
        return d, size, size

    raise ValueError(f"Unknown barcode type: {bc_type!r}")


# ── Single-voucher renderer ────────────────────────────────────────────────
def _draw_voucher(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    vote_nr: int,
    v_type: str,
    barcode_value: str,
    bc_type: BarcodeType,
    code_font: str,
) -> None:
    """Render one voucher cell onto the canvas.

    Args:
        c:             Active ReportLab canvas.
        x:             Left edge of the voucher cell in points.
        y:             Bottom edge of the voucher cell in points.
        width:         Cell width in points.
        height:        Cell height in points.
        vote_nr:       Voting round number (1–9).
        v_type:        Vote type key (``J``, ``N``, or ``E``).
        barcode_value: Encoded string to render as barcode and plain text.
        bc_type:       Barcode format identifier.
        code_font:     Font name for the human-readable text line.
    """
    c.rect(x, y, width, height, stroke=1, fill=0)

    c.setFont("Helvetica-Bold", 17)
    c.drawString(x + 2 * mm, y + height - 10 * mm, f"Abstimmung {vote_nr}")

    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(x + width - 2 * mm, y + height - 10 * mm, _VOTE_LABELS[v_type])

    bc_obj, bc_w, _ = _make_barcode(barcode_value, bc_type)
    x_bc = x + (width - bc_w) / 2
    bc_obj.drawOn(c, x_bc, y + 8 * mm)

    c.setFillColorRGB(0, 0, 0)
    c.setFont(code_font, 10)
    c.drawCentredString(x + width / 2, y + 4 * mm, barcode_value)


# ── Public API ─────────────────────────────────────────────────────────────
def create_vouchers(
    excel_file: Path | str,
    output_pdf: Path | str,
    bc_type: BarcodeType = "Code128",
) -> None:
    """Generate a PDF of voting vouchers from shareholder data.

    One page is produced per shareholder. Each page contains up to
    ``NUM_VOTES`` rows and three columns (JA / NEIN / ENTH).

    Args:
        excel_file: Path to the Excel file with shareholder data.
            Required columns: ``sh_nr``, ``anz_akt``.
        output_pdf: Destination path for the generated PDF.
        bc_type:    Barcode format to use (default ``Code128``).

    Raises:
        FileNotFoundError: If *excel_file* does not exist.
    """
    code_font = _register_fonts()

    try:
        df = pd.read_excel(excel_file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Excel file not found: {excel_file}") from exc

    page_width, page_height = A4
    bon_width = (page_width - 2 * _MARGIN_X) / 3
    bon_height = (page_height - 2 * _MARGIN_Y) / _VOUCHERS_PER_PAGE

    c = canvas.Canvas(str(output_pdf), pagesize=A4)

    for _, row in df.iterrows():
        shnr = f"{int(row['sh_nr']):03d}"
        anzakt = f"{int(row['anz_akt']):03d}"

        for vote_nr in range(1, NUM_VOTES + 1):
            pos_on_page = ((vote_nr - 1) % _VOUCHERS_PER_PAGE) + 1
            y_pos = page_height - _MARGIN_Y - (pos_on_page * bon_height)

            for col_idx, v_type in enumerate(_VOTE_TYPES):
                x_pos = _MARGIN_X + (col_idx * bon_width)
                barcode_value = f"{vote_nr}{v_type}{shnr}.{anzakt}"
                _draw_voucher(
                    c=c,
                    x=x_pos,
                    y=y_pos,
                    width=bon_width,
                    height=bon_height,
                    vote_nr=vote_nr,
                    v_type=v_type,
                    barcode_value=barcode_value,
                    bc_type=bc_type,
                    code_font=code_font,
                )

            if vote_nr % _VOUCHERS_PER_PAGE == 0 and vote_nr < NUM_VOTES:
                c.showPage()

        c.showPage()

    c.save()


if __name__ == "__main__":
    pass
