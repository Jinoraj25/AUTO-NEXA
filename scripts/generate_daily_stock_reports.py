import os
import pandas as pd
import numpy as np

output_dir = os.path.join("data", "stock_reports")
os.makedirs(output_dir, exist_ok=True)

# Base list of PCV components and parts
parts_base = [
    {"part_no": "01104M12556", "desc": "HEX BOLT & NUT M12", "brand": "MARUTI", "category": "Mechanical Parts", "unit_cost": 45, "base_stock": 140},
    {"part_no": "26300-35505", "desc": "SPIN-ON OIL FILTER", "brand": "HYUNDAI", "category": "Consumables", "unit_cost": 280, "base_stock": 95},
    {"part_no": "58101-2VA70", "desc": "FRONT DISC BRAKE PAD SET", "brand": "HYUNDAI", "category": "Mechanical Parts", "unit_cost": 1250, "base_stock": 60},
    {"part_no": "0112AU300990B", "desc": "1 DIN CTR BOX DASHBOARD TRIM", "brand": "MAHINDRA", "category": "Body Parts", "unit_cost": 850, "base_stock": 35},
    {"part_no": "544692000149", "desc": "SEAT SUB PART ASSEMBLY", "brand": "TATA", "category": "Body Parts", "unit_cost": 2100, "base_stock": 25},
    {"part_no": "18846-11070", "desc": "IRIDIUM SPARK PLUG", "brand": "HYUNDAI", "category": "Electrical Parts", "unit_cost": 420, "base_stock": 180},
    {"part_no": "16546-AA120", "desc": "ENGINE AIR FILTER ELEMENT", "brand": "MARUTI", "category": "Consumables", "unit_cost": 310, "base_stock": 110},
    {"part_no": "31112-1G000", "desc": "FUEL FILTER CARTRIDGE", "brand": "MARUTI", "category": "Consumables", "unit_cost": 540, "base_stock": 70},
    {"part_no": "9999900171AS", "desc": "RADIATOR CAP HYBRID", "brand": "HYUNDAI", "category": "Mechanical Parts", "unit_cost": 190, "base_stock": 85},
    {"part_no": "48820-02030", "desc": "FRONT STABILIZER LINK", "brand": "TOYOTA", "category": "Mechanical Parts", "unit_cost": 920, "base_stock": 45},
    {"part_no": "43512-0D160", "desc": "FRONT BRAKE ROTOR DISC", "brand": "TOYOTA", "category": "Mechanical Parts", "unit_cost": 2400, "base_stock": 30},
    {"part_no": "90919-01253", "desc": "SPARK PLUG DUAL GROOVE", "brand": "TOYOTA", "category": "Electrical Parts", "unit_cost": 380, "base_stock": 200}
]

# Generate daily files for 01-09-2026 to 09-09-2026
dates = [f"{day:02d}-09-2026" for day in range(1, 10)]

np.random.seed(42)

for day_idx, d_str in enumerate(dates):
    rows = []
    for p_idx, p in enumerate(parts_base):
        # Simulate realistic daily stock movements (sales consumption & stock replenishment)
        stock_change = int(np.random.randint(-8, 12)) if day_idx > 0 else 0
        current_stock = max(5, p["base_stock"] + (day_idx * stock_change))
        
        rows.append({
            "PART_NO": p["part_no"],
            "DESCRIPTION": p["desc"],
            "BRAND": p["brand"],
            "CATEGORY": p["category"],
            "STOCK_QTY": current_stock,
            "UNIT_COST": p["unit_cost"],
            "TOTAL_VALUATION": current_stock * p["unit_cost"],
            "BIN_LOCATION": f"BIN-{(p_idx%6)+1:02d}-{(p_idx%4)+1}",
            "REPORT_DATE": d_str
        })
    
    df = pd.DataFrame(rows)
    file_path = os.path.join(output_dir, f"Stock_Report_{d_str}.xlsx")
    df.to_excel(file_path, index=False)
    print(f"Generated daily stock report: {file_path} ({len(df)} SKUs)")

print(f"SUCCESS: Generated {len(dates)} daily stock reports in {output_dir}")
