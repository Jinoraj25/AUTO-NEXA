import os
import subprocess
import shutil
import time

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
artifact_dir = r"C:\Users\SM0237\.gemini\antigravity\brain\1636294a-d621-4bf7-9e5b-ee6314791af6"
base_dir = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT"

views = [
    ("shot_oes_to_oes_hub_verified.png", "http://localhost:8000/index.html?tab=catalogue-oem-to-oes", 1600, 1250),
    ("shot_taxonomy_and_split_verified.png", "http://localhost:8000/index.html?tab=catalogue-dashboard", 1600, 1100),
    ("shot_catalog_ai_verified.png", "http://localhost:8000/index.html?tab=catalogue-ai", 1600, 1100),
]

for fname, url, w, h in views:
    out_path = os.path.join(base_dir, fname)
    if os.path.exists(out_path):
        os.remove(out_path)
    
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        f"--window-size={w},{h}",
        f"--screenshot={out_path}",
        "--virtual-time-budget=4000",
        url
    ]
    print(f"Capturing {fname} from {url}...")
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    time.sleep(1)
    
    if os.path.exists(out_path):
        dst = os.path.join(artifact_dir, fname)
        shutil.copy2(out_path, dst)
        sz = os.path.getsize(out_path)
        print(f"SUCCESS: {fname} saved ({sz} bytes). Copied to artifact: {dst}")
    else:
        print(f"FAILED: {fname} not found. Returncode: {res.returncode}, Stderr: {res.stderr}")
