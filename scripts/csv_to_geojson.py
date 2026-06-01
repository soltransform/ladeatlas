import json
import math
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent
CSV_PATH = ROOT / "data/raw/Ladesaeulenregister_BNetzA_2026-04-22.csv"
OUT_PATH = ROOT / "data/chargers.geojson"

df = pd.read_csv(CSV_PATH, sep=";", encoding="latin-1", skiprows=10, low_memory=False)
print(f"Loaded {len(df)} rows, {len(df.columns)} columns\n")

# --- 1. Ladeeinrichtungs-ID → int ---
df["Ladeeinrichtungs-ID"] = pd.to_numeric(df["Ladeeinrichtungs-ID"], errors="coerce")
print(f"1. Ladeeinrichtungs-ID: {df['Ladeeinrichtungs-ID'].isna().sum()} null/non-numeric")

# --- 2. Betreiber → strip ---
df["Betreiber"] = df["Betreiber"].str.strip()
print(f"2. Betreiber: {df['Betreiber'].isna().sum()} null")

# --- 3. Anzeigename (Karte) → strip ---
df["Anzeigename (Karte)"] = df["Anzeigename (Karte)"].str.strip()
print(f"3. Anzeigename (Karte): {df['Anzeigename (Karte)'].isna().sum()} null")

# --- 4. Status → strip, show unique ---
df["Status"] = df["Status"].str.strip()
print(f"4. Status:")
for val, count in df["Status"].value_counts(dropna=False).items():
    print(f"   {repr(val)}: {count}")

# --- 5. Art der Ladeeinrichtung → strip, show unique ---
df["Art der Ladeeinrichtung"] = df["Art der Ladeeinrichtung"].str.strip()
print(f"5. Art der Ladeeinrichtung:")
for val, count in df["Art der Ladeeinrichtung"].value_counts(dropna=False).items():
    print(f"   {repr(val)}: {count}")

# --- 6. Anzahl Ladepunkte → int ---
df["Anzahl Ladepunkte"] = pd.to_numeric(df["Anzahl Ladepunkte"], errors="coerce")
null_lp = df["Anzahl Ladepunkte"].isna().sum()
bad_lp = (df["Anzahl Ladepunkte"] <= 0).sum()
print(f"6. Anzahl Ladepunkte: {null_lp} null, {bad_lp} <= 0")

# --- 7. Nennleistung Ladeeinrichtung [kW] → German float ---
def to_float(val):
    if pd.isna(val):
        return None
    try:
        return float(str(val).replace(",", "."))
    except ValueError:
        return None

col_nenn = "Nennleistung Ladeeinrichtung [kW]"
df[col_nenn] = df[col_nenn].apply(to_float)
null_nenn = df[col_nenn].isna().sum()
neg_nenn = (df[col_nenn] <= 0).sum()
print(f"7. {col_nenn}: {null_nenn} null/unparseable, {neg_nenn} <= 0, range {df[col_nenn].min()}-{df[col_nenn].max()}")

# --- 8. Inbetriebnahmedatum → ISO date ---
def to_iso_date(val):
    if pd.isna(val):
        return None
    try:
        return pd.to_datetime(str(val), format="%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        return val
df["Inbetriebnahmedatum"] = df["Inbetriebnahmedatum"].apply(to_iso_date)
print(f"8. Inbetriebnahmedatum: {df['Inbetriebnahmedatum'].isna().sum()} null")

# --- 9. Straße → strip ---
df["Straße"] = df["Straße"].str.strip()
print(f"9. Straße: {df['Straße'].isna().sum()} null")

# --- 10. Hausnummer → strip, keep as string ---
hn = df["Hausnummer"]
hn_null = hn.isna().sum()
hn = hn.where(hn.isna(), hn.astype(str).str.strip().str.replace(r'\.0$', '', regex=True))
df["Hausnummer"] = hn
print(f"10. Hausnummer: {hn_null} null")

# --- 11. Adresszusatz → strip ---
df["Adresszusatz"] = df["Adresszusatz"].str.strip()
print(f"11. Adresszusatz: {df['Adresszusatz'].isna().sum()} null")

# --- 12. Postleitzahl → strip, keep as string (leading zeros) ---
df["Postleitzahl"] = df["Postleitzahl"].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
df.loc[df["Postleitzahl"] == "nan", "Postleitzahl"] = None
print(f"12. Postleitzahl: {df['Postleitzahl'].isna().sum()} null")

# --- 13. Ort → strip ---
df["Ort"] = df["Ort"].str.strip()
print(f"13. Ort: {df['Ort'].isna().sum()} null")

# --- 14. Kreis/kreisfreie Stadt → strip ---
df["Kreis/kreisfreie Stadt"] = df["Kreis/kreisfreie Stadt"].str.strip()
print(f"14. Kreis/kreisfreie Stadt: {df['Kreis/kreisfreie Stadt'].isna().sum()} null")

# --- 15. Bundesland → strip, show unique ---
df["Bundesland"] = df["Bundesland"].str.strip()
print(f"15. Bundesland ({df['Bundesland'].nunique()} unique):")
for val, count in df["Bundesland"].value_counts(dropna=False).items():
    print(f"   {repr(val)}: {count}")

# --- 16. Breitengrad → German float ---
df["Breitengrad"] = df["Breitengrad"].apply(to_float)
null_lat = df["Breitengrad"].isna().sum()
print(f"16. Breitengrad: {null_lat} null, range {df['Breitengrad'].min()}-{df['Breitengrad'].max()}")

# --- 17. Längengrad → German float ---
df["Längengrad"] = df["Längengrad"].apply(to_float)
null_lon = df["Längengrad"].isna().sum()
print(f"17. Längengrad: {null_lon} null, range {df['Längengrad'].min()}-{df['Längengrad'].max()}")

# --- 18. Standortbezeichnung → strip ---
df["Standortbezeichnung"] = df["Standortbezeichnung"].str.strip()
print(f"18. Standortbezeichnung: {df['Standortbezeichnung'].isna().sum()} null")

# --- 19. Informationen zum Parkraum → strip ---
df["Informationen zum Parkraum"] = df["Informationen zum Parkraum"].str.strip()
print(f"19. Informationen zum Parkraum: {df['Informationen zum Parkraum'].isna().sum()} null")

# --- 20. Bezahlsysteme → strip ---
df["Bezahlsysteme"] = df["Bezahlsysteme"].str.strip()
print(f"20. Bezahlsysteme: {df['Bezahlsysteme'].isna().sum()} null")

# --- 21. Öffnungszeiten → strip ---
df["Öffnungszeiten"] = df["Öffnungszeiten"].str.strip()
print(f"21. Öffnungszeiten: {df['Öffnungszeiten'].isna().sum()} null")

# --- 22. Öffnungszeiten: Wochentage → strip ---
df["Öffnungszeiten: Wochentage"] = df["Öffnungszeiten: Wochentage"].str.strip()
print(f"22. Öffnungszeiten: Wochentage: {df['Öffnungszeiten: Wochentage'].isna().sum()} null")

# --- 23. Öffnungszeiten: Tageszeiten → strip ---
df["Öffnungszeiten: Tageszeiten"] = df["Öffnungszeiten: Tageszeiten"].str.strip()
print(f"23. Öffnungszeiten: Tageszeiten: {df['Öffnungszeiten: Tageszeiten'].isna().sum()} null")

# --- 24. Steckertypen1 → strip, show unique ---
df["Steckertypen1"] = df["Steckertypen1"].str.strip()
print(f"24. Steckertypen1 ({df['Steckertypen1'].nunique()} unique):")
for val, count in df["Steckertypen1"].value_counts(dropna=False).head(15).items():
    print(f"   {repr(val)}: {count}")

# --- 25. Nennleistung Stecker1 → German float ---
df["Nennleistung Stecker1"] = df["Nennleistung Stecker1"].apply(to_float)
null_ns1 = df["Nennleistung Stecker1"].isna().sum()
print(f"25. Nennleistung Stecker1: {null_ns1} null, range {df['Nennleistung Stecker1'].min()}-{df['Nennleistung Stecker1'].max()}")

# --- 26. EVSE-ID1 → strip ---
df["EVSE-ID1"] = df["EVSE-ID1"].str.strip()
print(f"26. EVSE-ID1: {df['EVSE-ID1'].isna().sum()} null")

# --- 27. Public Key1 → strip ---
df["Public Key1"] = df["Public Key1"].str.strip()
print(f"27. Public Key1: {df['Public Key1'].isna().sum()} null")

# --- 28. Steckertypen2 → strip ---
df["Steckertypen2"] = df["Steckertypen2"].str.strip()
print(f"28. Steckertypen2: {df['Steckertypen2'].isna().sum()} null")

# --- 29. Nennleistung Stecker2 → German float ---
df["Nennleistung Stecker2"] = df["Nennleistung Stecker2"].apply(to_float)
null_ns2 = df["Nennleistung Stecker2"].isna().sum()
print(f"29. Nennleistung Stecker2: {null_ns2} null")

# --- 30. EVSE-ID2 → strip ---
df["EVSE-ID2"] = df["EVSE-ID2"].str.strip()
print(f"30. EVSE-ID2: {df['EVSE-ID2'].isna().sum()} null")

# --- 31. Public Key2 → strip ---
df["Public Key2"] = df["Public Key2"].str.strip()
print(f"31. Public Key2: {df['Public Key2'].isna().sum()} null")

# --- 32. Steckertypen3 → strip ---
df["Steckertypen3"] = df["Steckertypen3"].str.strip()
print(f"32. Steckertypen3: {df['Steckertypen3'].isna().sum()} null")

# --- 33. Nennleistung Stecker3 → German float ---
df["Nennleistung Stecker3"] = df["Nennleistung Stecker3"].apply(to_float)
print(f"33. Nennleistung Stecker3: {df['Nennleistung Stecker3'].isna().sum()} null")

# --- 34. EVSE-ID3 → strip ---
df["EVSE-ID3"] = df["EVSE-ID3"].str.strip()
print(f"34. EVSE-ID3: {df['EVSE-ID3'].isna().sum()} null")

# --- 35. Public Key3 → strip ---
df["Public Key3"] = df["Public Key3"].str.strip()
print(f"35. Public Key3: {df['Public Key3'].isna().sum()} null")

# --- 36. Steckertypen4 → strip ---
df["Steckertypen4"] = df["Steckertypen4"].str.strip()
print(f"36. Steckertypen4: {df['Steckertypen4'].isna().sum()} null")

# --- 37. Nennleistung Stecker4 → German float ---
df["Nennleistung Stecker4"] = df["Nennleistung Stecker4"].apply(to_float)
print(f"37. Nennleistung Stecker4: {df['Nennleistung Stecker4'].isna().sum()} null")

# --- 38. EVSE-ID4 → strip ---
df["EVSE-ID4"] = df["EVSE-ID4"].str.strip()
print(f"38. EVSE-ID4: {df['EVSE-ID4'].isna().sum()} null")

# --- 39. Public Key4 → strip ---
df["Public Key4"] = df["Public Key4"].str.strip()
print(f"39. Public Key4: {df['Public Key4'].isna().sum()} null")

# --- 40. Steckertypen5 → strip ---
df["Steckertypen5"] = df["Steckertypen5"].str.strip()
print(f"40. Steckertypen5: {df['Steckertypen5'].isna().sum()} null")

# --- 41. Nennleistung Stecker5 → German float ---
df["Nennleistung Stecker5"] = df["Nennleistung Stecker5"].apply(to_float)
print(f"41. Nennleistung Stecker5: {df['Nennleistung Stecker5'].isna().sum()} null")

# --- 42. EVSE-ID5 → strip ---
df["EVSE-ID5"] = df["EVSE-ID5"].str.strip()
print(f"42. EVSE-ID5: {df['EVSE-ID5'].isna().sum()} null")

# --- 43. Public Key5 → strip ---
df["Public Key5"] = df["Public Key5"].str.strip()
print(f"43. Public Key5: {df['Public Key5'].isna().sum()} null")

# --- 44. Steckertypen6 → strip ---
df["Steckertypen6"] = df["Steckertypen6"].str.strip()
print(f"44. Steckertypen6: {df['Steckertypen6'].isna().sum()} null")

# --- 45. Nennleistung Stecker6 → German float ---
df["Nennleistung Stecker6"] = df["Nennleistung Stecker6"].apply(to_float)
print(f"45. Nennleistung Stecker6: {df['Nennleistung Stecker6'].isna().sum()} null")

# --- 46. EVSE-ID6 → strip ---
df["EVSE-ID6"] = df["EVSE-ID6"].str.strip()
print(f"46. EVSE-ID6: {df['EVSE-ID6'].isna().sum()} null")

# --- 47. Public Key6 → strip ---
df["Public Key6"] = df["Public Key6"].str.strip()
print(f"47. Public Key6: {df['Public Key6'].isna().sum()} null")

# --- Write GeoJSON ---
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
