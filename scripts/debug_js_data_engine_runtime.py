import re, json

data_engine_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\data-engine.js"
with open(data_engine_path, "r", encoding="utf-8") as f:
    js_code = f.read()

print(f"Read js/data-engine.js ({len(js_code):,} bytes, {len(js_code.splitlines()):,} lines)")

# Search for any undeclared variable assignments, broken object literals, or trailing commas/syntax issues
lines = js_code.splitlines()

# Check for method invocations on 'this' inside DataEngine object literal
methods_called_on_this = set(re.findall(r'this\.([a-zA-Z0-9_]+)\s*\(', js_code))
methods_defined = set(re.findall(r'([a-zA-Z0-9_]+)\s*\([^\)]*\)\s*\{', js_code))

print("\n--- Methods called on 'this' ---")
print(sorted(list(methods_called_on_this)))

missing_methods = methods_called_on_this - methods_defined
print("\n--- Methods called on 'this' but NOT defined in file ---")
print(missing_methods)

# Check for any places where db property is accessed before initialization
db_accesses = [i+1 for i, line in enumerate(lines) if 'this.db.' in line]
print(f"\n'this.db' referenced on {len(db_accesses)} lines.")
