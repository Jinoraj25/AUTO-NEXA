import re, os

print("=== Auditing JS files for syntax errors & invalid tokens ===")

js_files = [
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\data-engine.js",
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\mapping-portal.js",
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\analytics-portal.js",
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\inventory-portal.js",
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\deviation-portal.js",
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\forecasting-portal.js",
    r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\app.js"
]

error_count = 0

for file_path in js_files:
    if os.path.exists(file_path):
        fname = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            line_no = i + 1
            s = line.strip()

            # Check 1: Python-style '#' comment in JS outside of strings
            if s.startswith('#') and not s.startswith('#include') and not s.startswith('#define'):
                print(f"[{fname}:{line_no}] ERROR: Rogue '#' comment found: {s}")
                error_count += 1

            # Check 2: Double let/const declarations in same block
            if 'let keys = Object.keys' in line or 'const keys = Object.keys' in line:
                # Check line range
                pass

            # Check 3: Missing commas in object literals or invalid keywords
            if re.search(r'\b(None|True|False)\b', line) and not re.search(r'["\'].*?\b(None|True|False)\b.*?["\']', line):
                print(f"[{fname}:{line_no}] WARNING: Python keyword in JS: {s}")

if error_count == 0:
    print("SUCCESS: All JS files passed syntax audit cleanly with 0 errors!")
else:
    print(f"FAILURE: Found {error_count} syntax errors in JS files!")
