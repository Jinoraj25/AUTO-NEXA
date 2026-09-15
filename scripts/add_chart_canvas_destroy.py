import os
import re

js_dir = "js"
files = [f for f in os.listdir(js_dir) if f.endswith(".js")]

for fname in files:
    fpath = os.path.join(js_dir, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    canvas_ids = set(re.findall(r"document\.getElementById\(['\"](chart-[^'\"]+)['\"]\)", content))
    print(f"File {fname} has canvas IDs:", canvas_ids)
    
    modified = content
    for cid in canvas_ids:
        guard = f"if (typeof Chart !== 'undefined') {{ var _c = Chart.getChart('{cid}'); if (_c) _c.destroy(); }}\n"
        if f"Chart.getChart('{cid}')" not in modified and f'Chart.getChart("{cid}")' not in modified:
            # Look for canvas assignment or context assignment for this canvas ID
            pattern = re.compile(rf"(const|let|var)\s+(\w+)\s*=\s*document\.getElementById\(['\"]{re.escape(cid)}['\"]\)")
            if pattern.search(modified):
                modified = pattern.sub(rf"{guard}    \1 \2 = document.getElementById('{cid}')", modified)

    if modified != content:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(modified)
        print(f"Updated {fname} with Chart destroy guards.")
    else:
        print(f"No changes needed for {fname}.")
