"""
Test data generator for the voting voucher pipeline.
Version: 1.1.0

Creates synthetic shareholder data and writes it to an Excel file.
Share counts follow an exponential-like distribution so that most
shareholders own few shares and only a handful own many.
"""

__version__ = "1.1.0"

import random
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd

from utils.config import EXCEL_FILENAME, NUM_SHAREHOLDERS, MAX_SHARES

_NAMES: list[str] = [
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber",
    "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
]
_FIRST_NAMES: list[str] = [
    "Thomas", "Andreas", "Michael", "Frank", "Stefan",
    "Christian", "Jan", "Erik", "Hans", "Peter",
]


@dataclass
class Shareholder:
    """Represents a single shareholder record.

    Attributes:
        sh_nr: Zero-padded 3-digit shareholder identifier (e.g. '007').
        name: Family name.
        Vorname: Given name.
        anz_akt: Number of shares owned (1 … MAX_SHARES).
    """

    sh_nr: str
    name: str
    Vorname: str
    anz_akt: int


def _generate_shareholder(index: int) -> Shareholder:
    """Create a single randomised Shareholder.

    Args:
        index: 1-based position; used as the shareholder number.

    Returns:
        A populated Shareholder dataclass instance.
    """
    return Shareholder(
        sh_nr=f"{index:03d}",
        name=random.choice(_NAMES),
        Vorname=random.choice(_FIRST_NAMES),
        # Cubic distribution: strong bias towards low share counts
        anz_akt=int((random.random() ** 3) * (MAX_SHARES - 1)) + 1,
    )


def generate_test_data(
    filename: Path = EXCEL_FILENAME,
    num_shareholders: int = NUM_SHAREHOLDERS,
) -> None:
    """Generate synthetic shareholder data and save it as an Excel file.

    Args:
        filename: Destination path for the Excel file.
        num_shareholders: Number of shareholder rows to create.

    Raises:
        OSError: If the target directory is not writable.
    """
    shareholders = [_generate_shareholder(i) for i in range(1, num_shareholders + 1)]
    df = pd.DataFrame([asdict(s) for s in shareholders])
    df.to_excel(filename, index=False)
    print(f"Test data created: {filename}")


if __name__ == "__main__":
    generate_test_data()
