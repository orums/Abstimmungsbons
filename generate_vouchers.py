"""
Voucher Generation Script
-------------------------
This script reads shareholder data from an Excel file and generates a PDF containing
voting vouchers. Each voucher includes a barcode and human-readable text representing
a specific vote for a shareholder.

Layout:
- Page size: A4
- Grid: 3 columns (JA, NEIN, ENTH) x 7 rows (Votes)
- Each row represents one voting round.

Barcode Format:
The barcode (and human-readable text) follows the structure: [VoteNr][Type][ShareholderNr].[ShareCount]
- VoteNr: Sequence number of the voting round (e.g., 1, 2, 3)
- Type: Choice (J=JA, N=NEIN, E=ENTH)
- ShareholderNr: 3-digit padded ID (e.g., 001)
- ShareCount: 3-digit padded number of shares (e.g., 050)
Example: '2N012.045' -> Voting round 2, NEIN, Shareholder #12, 45 shares.

Barcode Types & Characteristics:
- Code 128: High-density linear barcode. Supports all 128 ASCII characters. 
            Efficient and compact for alphanumeric data.
- Code 39:  Linear barcode. Standard version is limited; 'Extended' (used here) 
            supports full ASCII. Less dense than Code 128 (resulting in wider barcodes).
- QR Code:  2D matrix code. High data capacity and excellent error correction. 
            Designed for fast omnidirectional scanning.
- DataMatrix: 2D matrix code. Extremely compact even with small physical dimensions. 
            High data density, commonly used for marking small items.
"""

import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128, code39, qr
from reportlab.graphics.barcode.widgets import BarcodeECC200DataMatrix
from reportlab.graphics.shapes import Drawing
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from utils.config import EXCEL_FILENAME, NUM_VOTES

def register_fonts():
    """
    Attempts to register a monospaced font for the human-readable barcode text.
    Prioritizes Consolas (Windows), falls back to standard Courier-Bold.
    """
    # Try to register Consolas from Windows fonts directory for better readability
    font_path = "C:/Windows/Fonts/consola.ttf"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Consolas', font_path))
            return 'Consolas'
        except Exception:
            pass
    return 'Courier-Bold' # Standard PDF fallback

def create_vouchers(excel_file, output_pdf, bc_type="Code128"):
    """
    Generates a PDF file with voting vouchers.
    
    Args:
        excel_file (str/Path): Path to the Excel file containing shareholder data.
        output_pdf (str/Path): Path where the resulting PDF will be saved.
        bc_type (str): The type of barcode to generate (Code128, Code39, DataMatrix, QR).
    """
    code_font = register_fonts()
    
    # Load shareholder data
    try:
        df = pd.read_excel(excel_file)
    except FileNotFoundError:
        print(f"Error: {excel_file} not found.")
        return

    # Initialize PDF canvas
    c = canvas.Canvas(str(output_pdf), pagesize=A4)
    width, height = A4
    
    # Layout constants
    margin_x = 10 * mm
    margin_y = 15 * mm
    
    # 3 columns for JA, NEIN, ENTH
    bon_width = (width - 2 * margin_x) / 3
    
    # Vertically, we fit a fixed number of vouchers per page
    vouchers_per_page = 7
    bon_height = (height - 2 * margin_y) / vouchers_per_page
    
    # Mapping for voting options
    votes_list = ["J", "N", "E"]
    vote_labels = {"J": "JA", "N": "NEIN", "E": "ENTH"}

    # Process each shareholder from the Excel file
    for _, row in df.iterrows():
        # Format IDs with leading zeros (e.g., 001 instead of 1)
        shnr = f"{int(row['sh_nr']):03d}"
        anzakt = f"{int(row['anz_akt']):03d}"
        
        # Generate the requested number of voting rounds per shareholder
        for vote_nr in range(1, NUM_VOTES + 1):
            # Calculate vertical position on the current page
            pos_on_page = ((vote_nr - 1) % vouchers_per_page) + 1
            # Coordinate system: (0,0) is bottom-left. We calculate from top-down.
            y_pos = height - margin_y - (pos_on_page * bon_height)
            
            # Create three columns for the current voting round
            for col_idx, v_type in enumerate(votes_list):
                x_pos = margin_x + (col_idx * bon_width)
                
                # Draw the voucher border
                c.rect(x_pos, y_pos, bon_width, bon_height, stroke=1, fill=0)
                
                # Header: Voting round number
                c.setFont("Helvetica-Bold", 17)
                c.drawString(x_pos + 2*mm, y_pos + bon_height - 10*mm, f"Abstimmung {vote_nr}")
                
                # Label: Actionable choice (JA/NEIN/ENTH)
                c.setFont("Helvetica-Bold", 18)
                c.drawRightString(x_pos + bon_width - 2*mm, y_pos + bon_height - 10*mm, vote_labels[v_type])
                
                # Unique identifier string for this specific voucher
                # Format: [VoteNr][Type][ShareholderNr].[ShareCount]
                barcode_value = f"{vote_nr}{v_type}{shnr}.{anzakt}"
                
                # Barcode generation based on type
                if bc_type == "Code128":
                    barcode = code128.Code128(barcode_value, barHeight=15*mm, barWidth=0.35*mm)
                    x_bc = x_pos + (bon_width - barcode.width) / 2
                    barcode.drawOn(c, x_bc, y_pos + 8*mm)
                
                elif bc_type == "Code39":
                    # Extended39 supports more characters but is wider than standard Code39
                    barcode = code39.Extended39(barcode_value, barHeight=15*mm, barWidth=0.25*mm)
                    x_bc = x_pos + (bon_width - barcode.width) / 2
                    barcode.drawOn(c, x_bc, y_pos + 8*mm)
                
                elif bc_type == "DataMatrix":
                    # 2D Barcode (Square)
                    bc_size = 3.75*mm
                    barcode = BarcodeECC200DataMatrix(value=barcode_value)
                    barcode.width = bc_size
                    barcode.height = bc_size
                    barcode.x = 0; barcode.y = 0
                    x_bc = x_pos + (bon_width - bc_size) / 2
                    d = Drawing(bc_size, bc_size)
                    d.add(barcode)
                    d.drawOn(c, x_bc, y_pos + 9*mm)
                
                elif bc_type == "QR":
                    # 2D QR Code
                    from reportlab.graphics.barcode.qr import QrCodeWidget
                    qr_code = QrCodeWidget(barcode_value)
                    bc_size = 18*mm # Scaled for visibility
                    bounds = qr_code.getBounds()
                    qr_w = bounds[2] - bounds[0]
                    qr_h = bounds[3] - bounds[1]
                    # Transform is used to scale the QR widget to the desired mm size
                    d = Drawing(bc_size, bc_size, transform=[bc_size/qr_w, 0, 0, bc_size/qr_h, 0, 0])
                    d.add(qr_code)
                    x_bc = x_pos + (bon_width - bc_size) / 2
                    d.drawOn(c, x_bc, y_pos + 9*mm)

                # Human-readable text at the bottom of the voucher
                c.setFillColorRGB(0, 0, 0)
                c.setFont(code_font, 10)
                c.drawCentredString(x_pos + bon_width/2, y_pos + 4*mm, barcode_value)
            
            # If we've filled the page (7 rounds) or finished this shareholder, start a new page
            if vote_nr % vouchers_per_page == 0 and vote_nr < NUM_VOTES:
                c.showPage()
        
        # Each shareholder starts on a fresh page
        c.showPage()
    
    # Finalize the PDF
    c.save()

if __name__ == "__main__":
    # The entry point for this script is typically main.py, 
    # but individual tests can be executed here if needed.
    pass
