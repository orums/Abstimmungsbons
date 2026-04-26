"""
Entry point for the voting voucher generation pipeline.
Version: 1.1.0

Runs three stages in sequence:
    1. Generate synthetic shareholder data (Excel).
    2. Render one PDF per barcode type (Code128, Code39, DataMatrix, QR).
"""

__version__ = "1.1.0"

from generate_test_data import generate_test_data
from generate_vouchers import create_vouchers
from utils.config import BARCODE_VARIATIONS, EXCEL_FILENAME, get_safe_path


def main() -> None:
    """Run the full voucher generation pipeline.

    Generates test data, then produces one PDF per configured barcode variant.
    Output files are written to the ``data/`` directory.
    """
    print("--- Voting Voucher Generator ---")

    print(f"Step 1: Generating test data in {EXCEL_FILENAME}...")
    generate_test_data()

    print(f"Step 2: Creating {len(BARCODE_VARIATIONS)} PDF variations...")
    for variation in BARCODE_VARIATIONS:
        safe_path = get_safe_path(variation.filename)
        print(f"  > Generating {variation.type} at {safe_path.name}...")
        create_vouchers(
            excel_file=EXCEL_FILENAME,
            output_pdf=safe_path,
            bc_type=variation.type,
        )

    print("\nSuccess! All versions created in the 'data' folder.")


if __name__ == "__main__":
    main()
