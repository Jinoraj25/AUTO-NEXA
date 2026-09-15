import json
import gzip
import os

print("=== Checking aggregate_master_rules.json ===")
gz_path = os.path.join("data", "aggregate_master_rules.json.gz")
raw_path = os.path.join("data", "aggregate_master_rules.json")
data = None
if os.path.exists(gz_path):
    with gzip.open(gz_path, "rt", encoding="utf-8") as f:
        data = json.load(f)
elif os.path.exists(raw_path):
    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)

if data:
    rules = data.get("aggregateMaster", [])
    print(f"Total rules: {len(rules)}")
    if rules:
        print("Sample Rule 0:", rules[0])
        print("Sample Rule 1:", rules[1])
else:
    print("NO DATA FOUND FOR aggregate_master_rules")

print("\n=== Checking sales_cache.json ===")
sales_gz = os.path.join("data", "sales_cache.json.gz")
sales_raw = os.path.join("data", "sales_cache.json")
sales_data = None
if os.path.exists(sales_gz):
    with gzip.open(sales_gz, "rt", encoding="utf-8") as f:
        sales_data = json.load(f)
elif os.path.exists(sales_raw):
    with open(sales_raw, "r", encoding="utf-8") as f:
        sales_data = json.load(f)

if sales_data:
    print("Sales Cache Keys:", list(sales_data.keys()))
    if "momTrend" in sales_data:
        print("momTrend sample:", sales_data["momTrend"][:2])
    if "pmsIntelligence" in sales_data:
        print("pmsIntelligence sample:", sales_data["pmsIntelligence"][:2])
else:
    print("NO DATA FOUND FOR sales_cache")

print("\n=== Checking stock_cache.json ===")
stock_gz = os.path.join("data", "stock_cache.json.gz")
stock_raw = os.path.join("data", "stock_cache.json")
stock_data = None
if os.path.exists(stock_gz):
    with gzip.open(stock_gz, "rt", encoding="utf-8") as f:
        stock_data = json.load(f)
elif os.path.exists(stock_raw):
    with open(stock_raw, "r", encoding="utf-8") as f:
        stock_data = json.load(f)

if stock_data:
    print("Stock Cache Keys:", list(stock_data.keys()))
    if "dates" in stock_data:
        print("Stock dates:", stock_data["dates"])
    if "valuationTrend" in stock_data:
        print("valuationTrend sample:", stock_data["valuationTrend"])
else:
    print("NO DATA FOUND FOR stock_cache")
