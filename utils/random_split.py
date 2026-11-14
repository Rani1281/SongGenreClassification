"""Random track-level split: stratified by genre, grouped by file hash.

Works on a TRACK-level DataFrame (one row per track, before windowing) that
has a genre column and a file-hash column. Tracks sharing a hash always land
in the same split. Windows inherit their track's split afterwards.

Split B (same proportions as Sturm):  fractions=(0.48, 0.21, 0.31)
Split C (phase 1 proportions):        fractions=(0.81, 0.09, 0.10)
"""
import numpy as np
import pandas as pd

SPLIT_NAMES = ("train", "val", "test")


def random_split(df, fractions=(0.48, 0.21, 0.31), seed=0,
                 genre_col="genre", group_col="file_hash"):
    """Return a copy of df with a 'split' column ('train' / 'val' / 'test')."""
    assert abs(sum(fractions) - 1.0) < 1e-9, "fractions must sum to 1"
    rng = np.random.default_rng(seed)
    boundaries = np.cumsum(fractions)  # e.g. [0.48, 0.69, 1.0]
    group_to_split = {}

    for _, g in df.groupby(genre_col):
        sizes = g.groupby(group_col).size()
        groups = sizes.index.to_numpy().copy()
        rng.shuffle(groups)
        n, seen = len(g), 0
        for grp in groups:
            # a group goes to the split whose interval contains its start position
            idx = min(np.searchsorted(boundaries, seen / n, side="right"),
                      len(SPLIT_NAMES) - 1)
            group_to_split[grp] = SPLIT_NAMES[idx]
            seen += sizes[grp]

    out = df.copy()
    out["split"] = out[group_col].map(group_to_split)
    return out


def check_split(df, genre_col="genre", group_col="file_hash"):
    """Sanity checks + a genre x split count table."""
    assert df["split"].notna().all(), "unassigned tracks"
    leaked = df.groupby(group_col)["split"].nunique()
    assert (leaked == 1).all(), f"{(leaked > 1).sum()} hashes span several splits"
    print("overall fractions:\n", df["split"].value_counts(normalize=True).round(3))
    return pd.crosstab(df[genre_col], df["split"])[list(SPLIT_NAMES)]


if __name__ == "__main__":
    # tiny synthetic demo: 10 genres x 100 tracks, a few duplicated hashes
    rows = []
    for gi in range(10):
        for t in range(100):
            rows.append({"track_id": f"g{gi}.{t:05d}", "genre": f"g{gi}",
                         "file_hash": f"h{gi}_{t if t % 25 else t - 1}"})
    tracks = pd.DataFrame(rows)
    split = random_split(tracks, seed=0)
    print(check_split(split))
