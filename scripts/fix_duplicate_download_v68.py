import os

print("=== Fixing Duplicate Download & Debouncing in Mapping Portal (v68) ===")

mapping_portal_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\mapping-portal.js"
with open(mapping_portal_path, "r", encoding="utf-8") as f:
    mp_content = f.read()

# 1. Remove duplicate addEventListener for btn-export-mapped in init()
old_init_binding = """    // Export Mapped Excel
    const exportBtn = document.getElementById('btn-export-mapped');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => this.exportMappedExcel());
    }"""

new_init_binding = """    // Export Mapped Excel (Triggered via HTML onclick to prevent duplicate downloads)"""

if old_init_binding in mp_content:
    mp_content = mp_content.replace(old_init_binding, new_init_binding)
    print("Removed duplicate addEventListener binding for btn-export-mapped in js/mapping-portal.js")

# 2. Add debouncing execution lock in exportMappedExcel()
old_export_start = """  exportMappedExcel() {"""

new_export_start = """  exportMappedExcel() {
    if (this._isExporting) {
      console.warn("Export already in progress, suppressing duplicate call.");
      return;
    }
    this._isExporting = true;
    setTimeout(() => { this._isExporting = false; }, 3000);"""

if old_export_start in mp_content and "if (this._isExporting)" not in mp_content:
    mp_content = mp_content.replace(old_export_start, new_export_start, 1)
    print("Added debouncing lock to exportMappedExcel() in js/mapping-portal.js")

with open(mapping_portal_path, "w", encoding="utf-8") as f:
    f.write(mp_content)

print("Done updating js/mapping-portal.js!")
