import pandas as pd
import random
import math
from utils.config import EXCEL_FILENAME, NUM_SHAREHOLDERS, MAX_SHARES

def generate_test_data(filename=EXCEL_FILENAME, num_shareholders=NUM_SHAREHOLDERS):
    names = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann"]
    first_names = ["Thomas", "Andreas", "Michael", "Frank", "Stefan", "Christian", "Jan", "Erik", "Hans", "Peter"]
    
    data = []
    for i in range(1, num_shareholders + 1):
        sh_nr = f"{i:03d}"
        name = random.choice(names)
        vorname = random.choice(first_names)
        
        # Decreasing probability: Using an exponential-like distribution
        # Most values will be small, few will be near MAX_SHARES
        # We use random.random()**3 to create a strong bias towards 0, then scale it.
        anz_akt = int((random.random()**3) * (MAX_SHARES - 1)) + 1
        
        data.append({
            "sh_nr": sh_nr,
            "name": name,
            "Vorname": vorname,
            "anz_akt": anz_akt
        })
    
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Test data created: {filename}")

if __name__ == "__main__":
    generate_test_data()
