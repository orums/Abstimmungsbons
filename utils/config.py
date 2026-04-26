from pathlib import Path

# Data Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXCEL_FILENAME = DATA_DIR / "test_data.xlsx"

# Barcode PDF definitions
BARCODE_VARIATIONS = [
    {"type": "Code128", "filename": DATA_DIR / "vouchers_code128.pdf"},
    {"type": "Code39", "filename": DATA_DIR / "vouchers_code39.pdf"},
    {"type": "DataMatrix", "filename": DATA_DIR / "vouchers_datamatrix.pdf"},
    {"type": "QR", "filename": DATA_DIR / "vouchers_qr.pdf"},
]

# Business Logic
NUM_SHAREHOLDERS = 5
NUM_VOTES = 3  # Max 9 per page layout constraints
MAX_SHARES = 100 # Results in max 999 (3 digits)


# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_safe_path(base_path: Path) -> Path:
    """Returns the base_path if it's writeable, otherwise appends _1, _2, etc."""
    if not base_path.exists():
        return base_path
    
    # Try to open the file for appending to check for locks
    try:
        with open(base_path, 'ab'):
            pass
        return base_path
    except PermissionError:
        suffix = 1
        while True:
            new_path = base_path.with_stem(f"{base_path.stem}_{suffix}")
            if not new_path.exists():
                return new_path
            try:
                with open(new_path, 'ab'):
                    pass
                return new_path
            except PermissionError:
                suffix += 1
