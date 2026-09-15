import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=================================================================")
print("          FULL PROJECT CODEBASE AUDIT FROM SCRATCH              ")
print("=================================================================")

# 1. Read index.html
with open("index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

# Extract all IDs in index.html
html_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html_content))
print(f"\n[HTML Audit] Found {len(html_ids)} unique element IDs in index.html.")

# Extract all onclick handlers in index.html
html_onclicks = set(re.findall(r'onclick=["\']([^"\']+)["\']', html_content))
print(f"[HTML Audit] Found {len(html_onclicks)} inline onclick handlers in index.html.")

# 2. Inspect all JS files
js_dir = "js"
js_files = [os.path.join(js_dir, f) for f in os.listdir(js_dir) if f.endswith(".js")]
js_files.append("nexa-app.js")

js_get_element_ids = set()
js_onclick_calls = set()

for jf in js_files:
    if os.path.exists(jf):
        with open(jf, "r", encoding="utf-8") as f:
            code = f.read()
        
        # Find getElementById calls
        ids = re.findall(r"document\.getElementById\(['\"]([^'\"]+)['\"]\)", code)
        js_get_element_ids.update(ids)

print(f"\n[JS Audit] Total unique getElementById target IDs in JavaScript: {len(js_get_element_ids)}")

# Check missing IDs in HTML
missing_in_html = js_get_element_ids - html_ids
if missing_in_html:
    print(f"⚠️ WARNING: The following {len(missing_in_html)} IDs referenced in JS were NOT found in index.html:")
    for mid in sorted(missing_in_html):
        print(f"   - {mid}")
else:
    print("✅ PERFECT! All {len(js_get_element_ids)} element IDs referenced in JS exist in index.html!")

# 3. Check Chart Canvas IDs in HTML vs JS
canvas_ids_html = set(re.findall(r'<canvas[^>]*id=["\']([^"\']+)["\']', html_content))
print(f"\n[Canvas Audit] Canvas element IDs in index.html: {canvas_ids_html}")

for cid in canvas_ids_html:
    if f"Chart" in html_content or True:
        found_in_js = any(cid in open(jf, 'r', encoding='utf-8').read() for jf in js_files if os.path.exists(jf))
        print(f"   Canvas '{cid}': {'FOUND in JS' if found_in_js else '⚠️ MISSING IN JS'}")

print("\n=================================================================")
print("Audit complete.")
