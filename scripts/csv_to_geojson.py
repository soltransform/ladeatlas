import json
import math
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent
CSV_PATH = ROOT / "data/raw/Ladesaeulenregister_BNetzA_2026-04-22.csv"
OUT_PATH = ROOT / "data/chargers.geojson"


def parse_german_float(val):
    if pd.isna(val):
        return None
    if isinstance(val, str):
        try:
            return float(val.replace(",", "."))
        except ValueError:
            return None
    return float(val)


def parse_german_date(val):
    if pd.isna(val):
        return None
    try:
        return pd.to_datetime(val, format="%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        return val


df = pd.read_csv(CSV_PATH, sep=";", encoding="latin-1", skiprows=10, low_memory=False)

# Coordinates (mandatory for geometry)
df["Breitengrad"] = df["Breitengrad"].apply(parse_german_float)
df["Längengrad"] = df["Längengrad"].apply(parse_german_float)

# All Nennleistung columns (main + Stecker1–6)
for col in [c for c in df.columns if "Nennleistung" in c]:
    df[col] = df[col].apply(parse_german_float)

# Date
df["Inbetriebnahmedatum"] = df["Inbetriebnahmedatum"].apply(parse_german_date)

records = [
    {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row.items()}
    for row in df.to_dict(orient="records")
]

features = [
    {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [row["Längengrad"], row["Breitengrad"]]},
        "properties": row,
    }
    for row in records
]

geojson = {"type": "FeatureCollection", "features": features}

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, separators=(",", ":"))

print(f"Done: {len(features)} features → {OUT_PATH}")
