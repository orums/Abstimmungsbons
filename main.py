from generate_test_data import generate_test_data
from generate_vouchers import create_vouchers
from utils.config import EXCEL_FILENAME, BARCODE_VARIATIONS, get_safe_path

def main():
    print("--- Voting Voucher Generator ---")
    
    # 1. Generate Data
    print(f"Step 1: Generating test data in {EXCEL_FILENAME}...")
    generate_test_data()
    
    # 2. Generate PDF Variations
    print(f"Step 2: Creating {len(BARCODE_VARIATIONS)} PDF variations...")
    for variation in BARCODE_VARIATIONS:
        safe_pdf_path = get_safe_path(variation['filename'])
        print(f"  > Generating {variation['type']} at {safe_pdf_path.name}...")
        create_vouchers(
            excel_file=EXCEL_FILENAME, 
            output_pdf=safe_pdf_path, 
            bc_type=variation['type']
        )
    
    print("\nSuccess! All versions created in the 'data' folder.")

if __name__ == "__main__":
    main()
