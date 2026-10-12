import sqlite3
import pandas as pd

DB_PATH = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\data\overall_catalogue.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=" * 80)
print("1. BEFORE UPDATE: Brand counts for RANE and AUTOKOI")
print("=" * 80)

cur.execute("SELECT brand_name, COUNT(*) FROM overall_catalogue WHERE brand_name LIKE '%RANE%' OR brand_name LIKE '%AUTOKOI%' GROUP BY brand_name")
for r in cur.fetchall():
    print(f"Brand: '{r[0]}' | Count: {r[1]:,}")

print("\n2. Executing Updates...")

# 1. Update line code 039 or 'RANE' -> 'RANE MADRAS LIMITED'
cur.execute("UPDATE overall_catalogue SET brand_name = 'RANE MADRAS LIMITED' WHERE line_code = '039' OR line_code = '39' OR brand_name = 'RANE'")
u1 = cur.rowcount
print(f"   -> Updated {u1:,} rows for RANE -> RANE MADRAS LIMITED")

# 2. Update Autokoi / autokoi / AUTOKOI -> 'AUTOKOI'
cur.execute("UPDATE overall_catalogue SET brand_name = 'AUTOKOI' WHERE UPPER(brand_name) = 'AUTOKOI'")
u2 = cur.rowcount
print(f"   -> Standardized {u2:,} rows for AUTOKOI")

# 3. Standardize any remaining leading/trailing whitespace in brand_name
cur.execute("UPDATE overall_catalogue SET brand_name = TRIM(brand_name)")

conn.commit()

print("\n" + "=" * 80)
print("3. AFTER UPDATE: Brand counts for RANE MADRAS LIMITED and AUTOKOI")
print("=" * 80)

cur.execute("SELECT brand_name, COUNT(*) FROM overall_catalogue WHERE brand_name LIKE '%RANE%' OR brand_name LIKE '%AUTOKOI%' GROUP BY brand_name")
for r in cur.fetchall():
    print(f"Brand: '{r[0]}' | Count: {r[1]:,}")

# Check total unique brand count after cleanup
cur.execute("SELECT COUNT(DISTINCT brand_name) FROM overall_catalogue WHERE brand_name IS NOT NULL AND brand_name != ''")
total_brands = cur.fetchone()[0]
print(f"\nTotal Unique Brands in Database after standardization: {total_brands}")

conn.close()
