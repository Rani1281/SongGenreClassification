"""Update the filtered split manifests from analyzed_tracks.xlsx.

Requires openpyxl: python -m pip install openpyxl
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


PROJECT_DIR = Path(__file__).resolve().parent
WORKBOOK_PATH = PROJECT_DIR / "analyzed_tracks.xlsx"
SPLIT_DIR = PROJECT_DIR / "filtered_splits"
SPLIT_FILES = {
    "train": SPLIT_DIR / "train_filtered.txt",
    "test": SPLIT_DIR / "test_filtered.txt",
    "valid": SPLIT_DIR / "valid_filtered.txt",
}


def normalize_path(value: Any) -> str:
    """Return a comparable form of a song path from Excel or a manifest."""
    return str(value).strip().replace("\\", "/").removeprefix("./").casefold()


def read_manifest(path: Path) -> list[str]:
    """Read non-empty song paths, preserving their displayed spelling."""
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def get_rank(value: Any, row_number: int) -> int:
    try:
        numeric_rank = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid rank in workbook row {row_number}: {value!r}") from exc

    # Reject fractional or out-of-range values rather than silently truncating.
    if not numeric_rank.is_integer() or not 1 <= numeric_rank <= 10:
        raise ValueError(f"Invalid rank in workbook row {row_number}: {value!r}")

    return int(numeric_rank)


def update_manifests(add_to: str) -> None:
    workbook = load_workbook(WORKBOOK_PATH, read_only=True, data_only=True)
    try:
        worksheet = workbook.active
        rows = worksheet.iter_rows(values_only=True)
        header = next(rows, None)
        if header is None:
            raise ValueError("The workbook's active sheet is empty.")

        columns = {
            str(name).strip().casefold(): index
            for index, name in enumerate(header)
            if name is not None
        }
        missing = {"path", "rank"} - columns.keys()
        if missing:
            raise ValueError(f"Workbook is missing required column(s): {', '.join(sorted(missing))}")

        manifests = {name: read_manifest(path) for name, path in SPLIT_FILES.items()}

        # Validate and apply in memory before writing, so malformed workbook rows
        # cannot leave the three manifests only partly updated.
        for row_number, row in enumerate(rows, start=2):
            raw_path = row[columns["path"]] if columns["path"] < len(row) else None
            raw_rank = row[columns["rank"]] if columns["rank"] < len(row) else None
            if raw_path is None or not str(raw_path).strip():
                continue

            song_path = str(raw_path).strip().replace("\\", "/")
            song_key = normalize_path(song_path)
            rank = get_rank(raw_rank, row_number)
            locations = [
                name
                for name, lines in manifests.items()
                if any(normalize_path(line) == song_key for line in lines)
            ]

            if locations and rank <= 5:
                for name in locations:
                    manifests[name] = [
                        line for line in manifests[name]
                        if normalize_path(line) != song_key
                    ]
            elif not locations and rank > 5:
                manifests[add_to].append(song_path)

    finally:
        workbook.close()

    for name, path in SPLIT_FILES.items():
        contents = "\n".join(manifests[name])
        path.write_text(contents + ("\n" if contents else ""), encoding="utf-8")

    for name, path in SPLIT_FILES.items():
        print(f"{path.name}: {len(manifests[name])} songs")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove low-ranked songs and add missing high-ranked songs to filtered split files."
    )
    parser.add_argument(
        "--add-to",
        choices=SPLIT_FILES,
        default="train",
        help="split for missing songs with rank above 5 (default: train)",
    )
    args = parser.parse_args()

    if not WORKBOOK_PATH.is_file():
        raise FileNotFoundError(f"Workbook not found: {WORKBOOK_PATH}")
    missing_files = [path for path in SPLIT_FILES.values() if not path.is_file()]
    if missing_files:
        raise FileNotFoundError("Missing split file(s): " + ", ".join(map(str, missing_files)))

    update_manifests(args.add_to)


if __name__ == "__main__":
    main()
