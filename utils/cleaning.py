from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "googleplaystore.csv"


def _number(series):
    return pd.to_numeric(
        series.astype("string")
        .str.replace(",", "", regex=False)
        .str.replace("+", "", regex=False)
        .str.strip(),
        errors="coerce",
    )


def _size_mb(series):
    raw = series.astype("string").str.strip()
    value = pd.to_numeric(raw.str.extract(r"([0-9]*\.?[0-9]+)", expand=False), errors="coerce")
    value = value.mask(raw.str.contains("k", case=False, na=False), value / 1024.0)
    value = value.mask(raw.str.contains("varies with device", case=False, na=False), np.nan)
    return value


def _price(series):
    return pd.to_numeric(
        series.astype("string").str.replace("$", "", regex=False).str.strip(),
        errors="coerce",
    )


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.drop_duplicates().reset_index(drop=True)

    for col in ["Rating", "Reviews", "Installs"]:
        if col in df.columns:
            df[col] = _number(df[col])
    if "Size" in df.columns:
        df["Size_MB"] = _size_mb(df["Size"])
    if "Price" in df.columns:
        df["Price"] = _price(df["Price"])
    if "Last Updated" in df.columns:
        df["Last Updated"] = pd.to_datetime(df["Last Updated"], errors="coerce")

    if "App" in df.columns:
        df["App"] = df["App"].fillna("Unknown").astype(str).str.strip()
    if "Category" in df.columns:
        df["Category"] = df["Category"].fillna("Uncategorized").astype(str).str.strip().str.upper()
    if "Type" in df.columns:
        df["Type"] = df["Type"].fillna("Unknown").astype(str).str.strip()

    required = [c for c in ["App", "Category", "Rating", "Reviews", "Installs", "Size_MB"] if c in df.columns]
    if required:
        df = df.dropna(subset=required)
    if "Rating" in df.columns:
        df = df[df["Rating"].between(0, 5)]
    if "Reviews" in df.columns:
        df = df[df["Reviews"] >= 0]
    if "Installs" in df.columns:
        df = df[df["Installs"] >= 0]
    if "Size_MB" in df.columns:
        df = df[df["Size_MB"] > 0]
    return df.reset_index(drop=True)


def load_data(path=None) -> pd.DataFrame:
    file_path = Path(path) if path else DATA_FILE
    if not file_path.is_absolute():
        file_path = PROJECT_ROOT / file_path
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")
    return clean_data(pd.read_csv(file_path, low_memory=False))
