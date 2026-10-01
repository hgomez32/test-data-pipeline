import sqlite3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DATA = Path("data/train_FD001.txt")
OUT = Path("output")
OUT.mkdir(exist_ok=True)

COLS = ["unit", "cycle", "op1", "op2", "op3"] + [f"s{i}" for i in range(1, 22)]


def load(path):
    return pd.read_csv(path, sep=r"\s+", header=None, names=COLS)


def validate(df):
    """Basic data-quality checks, printed as a report."""
    print(f"Rows: {len(df):,} | Engines: {df['unit'].nunique()}")
    print(f"Missing values: {int(df.isna().sum().sum())}")
    print(f"Duplicate rows: {int(df.duplicated().sum())}")


def clean(df):
    df = df.drop_duplicates().sort_values(["unit", "cycle"]).reset_index(drop=True)
    sensors = [c for c in df.columns if c.startswith("s")]

    # Sensors that never change carry no information
    constant = [c for c in sensors if df[c].nunique() <= 1]
    df = df.drop(columns=constant)
    sensors = [c for c in sensors if c not in constant]
    print(f"Dropped constant sensors: {constant}")

    # Flag extreme readings (|z-score| > 4) instead of deleting them
    z = (df[sensors] - df[sensors].mean()) / df[sensors].std()
    df["outlier_flag"] = (z.abs() > 4).any(axis=1)

    # Remaining cycles before failure
    df["rul"] = df.groupby("unit")["cycle"].transform("max") - df["cycle"]
    return df, sensors


def summarize(df):
    summary = (
        df.groupby("unit")
        .agg(cycles_to_failure=("cycle", "max"), flagged_readings=("outlier_flag", "sum"))
        .reset_index()
    )
    summary.to_csv(OUT / "engine_summary.csv", index=False)
    print(summary.describe().round(1))
    return summary


def plot(df, summary):
    fig, ax = plt.subplots(figsize=(8, 4))
    for unit in [1, 2, 3]:
        d = df[df["unit"] == unit]
        ax.plot(d["cycle"], d["s11"], label=f"Engine {unit}")
    ax.set(title="Sensor 11 over engine life", xlabel="Cycle", ylabel="Sensor 11")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "sensor11_trend.png", dpi=150)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(summary["cycles_to_failure"], bins=20)
    ax.set(title="Cycles to failure by engine", xlabel="Cycles", ylabel="Engines")
    fig.tight_layout()
    fig.savefig(OUT / "lifetime_hist.png", dpi=150)


def to_sqlite(df):
    with sqlite3.connect(OUT / "engines.db") as conn:
        df.to_sql("readings", conn, if_exists="replace", index=False)


if __name__ == "__main__":
    raw = load(DATA)
    validate(raw)
    df, sensors = clean(raw)
    summary = summarize(df)
    plot(df, summary)
    to_sqlite(df)
    print("Done. See the output/ folder.")