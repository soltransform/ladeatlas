import json
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHARGERS = ROOT / "data/chargers.geojson"
STATES = ROOT / "data/bkg_states.geojson"

chargers = gpd.read_file(CHARGERS)
states = gpd.read_file(STATES)

print(f"Chargers: {len(chargers)}")
print(f"State polygons: {len(states)}")

# BKG has separate polygons for Bodensee parts — merge by state name
states_merged = states.dissolve(by="gen").reset_index()
print(f"States after dissolve: {len(states_merged)}")

# Spatial join: which state polygon does each charger actually fall in?
joined = gpd.sjoin(chargers, states_merged[["gen", "geometry"]], how="left", predicate="within")

# Compare CSV Bundesland vs. actual geographic state
joined["geo_state"] = joined["gen"]
mismatch = joined[joined["Bundesland"] != joined["geo_state"]]
no_match = joined[joined["geo_state"].isna()]

print(f"\nResults:")
print(f"  Matched (correct state): {len(joined) - len(mismatch) - len(no_match)}")
print(f"  Mismatched (wrong state): {len(mismatch) - len(no_match)}")
print(f"  Outside Germany entirely: {len(no_match)}")

if len(no_match) > 0:
    print(f"\n--- Outside Germany ({len(no_match)}) ---")
    for _, row in no_match.iterrows():
        print(f"  ID {row['Ladeeinrichtungs-ID']}: {row['Bundesland']} | {row['Straße']} {row['Hausnummer']}, {row['Postleitzahl']} {row['Ort']} | ({row.geometry.y:.4f}, {row.geometry.x:.4f})")

wrong_state = mismatch[mismatch["geo_state"].notna()]
if len(wrong_state) > 0:
    print(f"\n--- Wrong state ({len(wrong_state)}) ---")
    for _, row in wrong_state.iterrows():
        print(f"  ID {row['Ladeeinrichtungs-ID']}: CSV={row['Bundesland']} → Geo={row['geo_state']} | {row['Straße']} {row['Hausnummer']}, {row['Postleitzahl']} {row['Ort']} | ({row.geometry.y:.4f}, {row.geometry.x:.4f})")
