import sqlite3

DB_PATH = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\data\overall_catalogue.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=" * 80)
print("1. BEFORE FULL UPPERCASE STANDARDIZATION:")
print("=" * 80)

cur.execute("SELECT COUNT(DISTINCT brand_name) FROM overall_catalogue WHERE brand_name IS NOT NULL AND brand_name != ''")
before_cnt = cur.fetchone()[0]
print(f"Total Unique Brands Before: {before_cnt}")

# Update all brand names to UPPERCASE and TRIM whitespace
cur.execute("UPDATE overall_catalogue SET brand_name = UPPER(TRIM(brand_name)) WHERE brand_name IS NOT NULL")
conn.commit()

print("\n" + "=" * 80)
print("2. AFTER FULL UPPERCASE STANDARDIZATION:")
print("=" * 80)

cur.execute("SELECT COUNT(DISTINCT brand_name) FROM overall_catalogue WHERE brand_name IS NOT NULL AND brand_name != ''")
after_cnt = cur.fetchone()[0]
print(f"Total Unique Brands After:  {after_cnt}")
print(f"Merged Casing Variations:   {before_cnt - after_cnt} brands merged")

print("\nListing all cleaned unique brands:")
cur.execute("SELECT brand_name, COUNT(*) FROM overall_catalogue WHERE brand_name IS NOT NULL AND brand_name != '' GROUP BY brand_name ORDER BY brand_name")
all_clean = cur.fetchall()
for idx, (b, c) in enumerate(all_clean, 1):
    print(f"{idx:03d}. '{b}' -> {c:,} rows")

conn.close()
