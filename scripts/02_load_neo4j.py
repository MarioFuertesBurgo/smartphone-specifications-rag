# --- bootstrap para poder ejecutar desde cualquier sitio ---
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# --- fin bootstrap ---

import math
import pandas as pd
from app.neo4j_utils import get_driver, run_cypher, run_cypher_many

CSV_PATH = "data/smartphone-specification.csv"
BATCH_SIZE = 200
INR_TO_EUR = 0.0094

# (Opcional) Para desarrollo: borrar todo antes de cargar
WIPE = """
MATCH (n) DETACH DELETE n;
"""

CONSTRAINTS = """
CREATE CONSTRAINT phone_model_unique IF NOT EXISTS
FOR (p:Phone) REQUIRE p.model IS UNIQUE;

CREATE CONSTRAINT os_name_unique IF NOT EXISTS
FOR (o:OS) REQUIRE o.name IS UNIQUE;

CREATE CONSTRAINT chipset_name_unique IF NOT EXISTS
FOR (c:Chipset) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT network_name_unique IF NOT EXISTS
FOR (n:Network) REQUIRE n.name IS UNIQUE;

CREATE CONSTRAINT displaytype_name_unique IF NOT EXISTS
FOR (d:DisplayType) REQUIRE d.name IS UNIQUE;

CREATE CONSTRAINT memcardtype_name_unique IF NOT EXISTS
FOR (m:MemoryCardType) REQUIRE m.name IS UNIQUE;
"""

LOAD_BATCH = """
UNWIND $rows AS row
WITH row
WHERE row.model IS NOT NULL AND trim(row.model) <> ''

// Phone
MERGE (p:Phone {model: toLower(row.model)})
SET
  p.model_raw = row.model,
  p.price = row.price,
  p.rating = row.rating,
  p.volte = row.volte,
  p.nfc = row.nfc,
  p.ir_blaster = row.ir_blaster,
  p.ram_gb = row.ram_gb,
  p.storage_gb = row.storage_gb,
  p.battery_mah = row.battery_mah,
  p.screen_size_in = row.screen_size_in,
  p.refresh_rate_hz = row.refresh_rate_hz,
  p.rear_camera_mp_list = row.rear_camera_mp_list,
  p.rear_camera_count = row.rear_camera_count,
  p.front_camera_mp = row.front_camera_mp,
  p.memory_card_supported = row.memory_card_supported,
  p.text = row.text

// Relaciones "de grafo" (categorías compartidas)
WITH p, row

FOREACH (_ IN CASE WHEN row.os <> '' THEN [1] ELSE [] END |
  MERGE (o:OS {name: row.os})
  MERGE (p)-[:RUNS]->(o)
)

FOREACH (_ IN CASE WHEN row.chipset <> '' THEN [1] ELSE [] END |
  MERGE (c:Chipset {name: row.chipset})
  MERGE (p)-[:HAS_CHIPSET]->(c)
)

FOREACH (_ IN CASE WHEN row.network_type <> '' THEN [1] ELSE [] END |
  MERGE (n:Network {name: row.network_type})
  MERGE (p)-[:SUPPORTS_NETWORK]->(n)
)

FOREACH (_ IN CASE WHEN row.display_type <> '' THEN [1] ELSE [] END |
  MERGE (d:DisplayType {name: row.display_type})
  MERGE (p)-[:HAS_DISPLAY_TYPE]->(d)
)

// Solo si soporta tarjeta y hay tipo
FOREACH (_ IN CASE WHEN row.memory_card_supported = true AND row.memory_card_type <> '' THEN [1] ELSE [] END |
  MERGE (m:MemoryCardType {name: row.memory_card_type})
  MERGE (p)-[:SUPPORTS_MEMORY_CARD_TYPE]->(m)
);
"""

COUNT = "MATCH (p:Phone) RETURN count(p) AS n;"
REL_COUNT = """
MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS n ORDER BY n DESC;
"""

def to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return False
    s = str(v).strip().lower()
    return s in ("true", "1", "yes")

def to_int(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    try:
        return int(float(v))
    except:
        return None

def to_float(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    try:
        return float(v)
    except:
        return None

def build_text(row: dict) -> str:
    # Formato estable tipo key=value (suele ir muy bien para retrieval)
    return (
        f"Model={row.get('model','')}; "
        f"Price_EUR={row.get('price')}; "
        f"Rating={row.get('rating')}; "
        f"OS={row.get('os','')}; "
        f"Network={row.get('network_type','')}; "
        f"NFC={str(row.get('nfc')).lower()}; "
        f"VoLTE={str(row.get('volte')).lower()}; "
        f"IRBlaster={str(row.get('ir_blaster')).lower()}; "
        f"Chipset={row.get('chipset','')}; "
        f"RAM_GB={row.get('ram_gb')}; "
        f"Storage_GB={row.get('storage_gb')}; "
        f"Battery_mAh={row.get('battery_mah')}; "
        f"Screen_in={row.get('screen_size_in')}; "
        f"RefreshRate_Hz={row.get('refresh_rate_hz')}; "
        f"DisplayType={row.get('display_type','')}; "
        f"RearCameras={row.get('rear_camera_mp_list','')}; "
        f"RearCameraCount={row.get('rear_camera_count')}; "
        f"FrontCamera_MP={row.get('front_camera_mp')}; "
        f"MemoryCardSupported={str(row.get('memory_card_supported')).lower()}; "
        f"MemoryCardType={row.get('memory_card_type','')}"
    )

def main():
    df = pd.read_csv(CSV_PATH)

    rows = []
    for _, r in df.iterrows():
        model = r.get("model")
        if pd.isna(model) or str(model).strip() == "":
            continue

        price_inr = to_float(r.get("price"))
        price_eur = round(price_inr * INR_TO_EUR, 2) if price_inr is not None else None

        row = {
            "model": str(model).strip(),
            "price": price_eur,
            "rating": to_float(r.get("rating")),
            "os": "" if pd.isna(r.get("os")) else str(r.get("os")).strip(),
            "network_type": "" if pd.isna(r.get("network_type")) else str(r.get("network_type")).strip(),
            "volte": to_bool(r.get("VoLTE")),
            "nfc": to_bool(r.get("NFC")),
            "ir_blaster": to_bool(r.get("ir_blaster")),
            "chipset": "" if pd.isna(r.get("chipset")) else str(r.get("chipset")).strip(),
            "ram_gb": to_float(r.get("ram_gb")),
            "storage_gb": to_float(r.get("storage_gb")), 
            "battery_mah": to_int(r.get("battery_mah")),
            "screen_size_in": to_float(r.get("screen_size_in")),
            "refresh_rate_hz": to_float(r.get("refresh_rate_hz")),
            "display_type": "" if pd.isna(r.get("display_type")) else str(r.get("display_type")).strip(),
            "rear_camera_mp_list": "" if pd.isna(r.get("rear_camera_mp_list")) else str(r.get("rear_camera_mp_list")).strip(),
            "rear_camera_count": to_int(r.get("rear_camera_count")),
            "front_camera_mp": to_float(r.get("front_camera_mp")),
            "memory_card_supported": str(r.get("memory_card_supported", "")).strip() == "1",
            "memory_card_type": "" if pd.isna(r.get("memory_card_type")) else str(r.get("memory_card_type")).strip(),
        }
        row["text"] = build_text(row)
        rows.append(row)

    driver = get_driver()
    try:
        # Para desarrollo: limpia todo (si NO quieres esto, comenta la línea)
        run_cypher(driver, WIPE)

        run_cypher_many(driver, CONSTRAINTS)

        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i+BATCH_SIZE]
            run_cypher(driver, LOAD_BATCH, {"rows": batch})
            print(f"Inserted batch {i//BATCH_SIZE + 1} ({len(batch)} rows)")

        with driver.session() as s:
            n = s.run(COUNT).single()["n"]
            print(f"OK. Phones cargados: {n}")
            print("Relaciones creadas:")
            for rec in s.run(REL_COUNT):
                print(f"  {rec['rel']}: {rec['n']}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()
