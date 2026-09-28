import re, os

print("=== Fixing Syntax Errors & Verifying JS Files ===")

data_engine_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\data-engine.js"
with open(data_engine_path, "r", encoding="utf-8") as f:
    js_code = f.read()

# Fix python comment in JS
if "# Strategy 4" in js_code:
    js_code = js_code.replace("# Strategy 4", "// Strategy 4")
    print("Fixed '#' comment on line 11408 of js/data-engine.js")

with open(data_engine_path, "w", encoding="utf-8") as f:
    f.write(js_code)

# Check all JS files for any rogue '#' comments or syntax issues
js_files = [
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\data-engine.js",
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\mapping-portal.js",
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\analytics-portal.js",
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\inventory-portal.js",
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\deviation-portal.js",
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\forecasting-portal.js",
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\app.js"
]

for file_path in js_files:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for non-comment '#' lines
        for i, line in enumerate(content.splitlines()):
            stripped = line.strip()
            if stripped.startswith('#') and not stripped.startswith('#include') and not stripped.startswith('#define'):
                print(f"CRITICAL ERROR: Found '#' comment in {os.path.basename(file_path)} line {i+1}: {stripped}")

print("Verification complete!")
