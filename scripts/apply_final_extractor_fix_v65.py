import json
import re

def apply_final_extractor_fix():
    # 1. Update js/data-engine.js
    with open('js/data-engine.js', 'r', encoding='utf-8') as f:
        de_text = f.read()

    # Enhanced keywords list
    old_part_kws = "const partKeywords = ['partno', 'part number', 'part_number', 'itemcode', 'item code', 'item_code', 'manpart', 'material', 'sku', 'productno', 'article', 'lncode', 'part'];"
    new_part_kws = "const partKeywords = ['itemcode_rev', 'item_code_rev', 'item code_rev', 'itemcoderev', 'partno', 'part number', 'part_number', 'itemcode', 'item code', 'item_code', 'manpart', 'material', 'sku', 'productno', 'article', 'lncode', 'part'];"

    old_desc_kws = "const descKeywords = ['description', 'item description', 'item_description', 'part description', 'part_description', 'itemdesc', 'item desc', 'itemname', 'item name', 'item_name', 'desc', 'detail', 'specification', 'title'];"
    new_desc_kws = "const descKeywords = ['itemname', 'item name', 'item_name', 'description', 'item description', 'item_description', 'part description', 'part_description', 'itemdesc', 'item desc', 'desc', 'detail', 'specification', 'title', 'part name', 'product name'];"

    if old_part_kws in de_text:
        de_text = de_text.replace(old_part_kws, new_part_kws)
        print("Updated partKeywords in js/data-engine.js")

    if old_desc_kws in de_text:
        de_text = de_text.replace(old_desc_kws, new_desc_kws)
        print("Updated descKeywords in js/data-engine.js")

    # Update inspectColumnsByContent to handle itemcode_rev and itemname
    old_inspector = "const sample = rawRows.slice(0, 10);"
    new_inspector = """const sample = rawRows.slice(0, 15);
    const keys = Object.keys(sample[0]);

    // Check for exact normalized key matches first
    for (let k of keys) {
      const kNorm = k.toLowerCase().replace(/[^a-z0-9]/g, '');
      if (kNorm.includes('itemname') || kNorm.includes('itemdescription') || kNorm.includes('partdescription') || kNorm.includes('description')) {
        descCol = k;
      }
      if (kNorm.includes('itemcode') || kNorm.includes('partnumber') || kNorm.includes('partno') || kNorm.includes('itemcoderev')) {
        partCol = k;
      }
    }"""

    if 'const sample = rawRows.slice(0, 10);' in de_text:
        de_text = de_text.replace('const sample = rawRows.slice(0, 10);', new_inspector)
        print("Enhanced inspectColumnsByContent key matching in js/data-engine.js")

    # Update processSalesUpload row value fallback
    old_row_fallback = """      // Fallbacks if columns were unlabeled
      if (!partNo) {
        const firstVal = Object.values(row)[0];
        partNo = firstVal ? String(firstVal) : `PART-${idx+1001}`;
      }
      if (!desc) {
        const secondVal = Object.values(row)[1];
        desc = secondVal ? String(secondVal) : "";
      }"""

    new_row_fallback = """      // Robust content-based fallback for desc and partNo if column names were unmapped
      if (!desc || desc.trim() === "" || desc.toLowerCase() === "nan") {
        const vals = Object.values(row).map(v => String(v || '').trim()).filter(v => v.length > 2 && v.toLowerCase() !== 'nan');
        const descCand = vals.find(v => (v.includes(' ') || v.length > 8) && !/^[0-9]+$/.test(v));
        if (descCand) desc = descCand;
      }
      if (!partNo || partNo.trim() === "" || partNo.toLowerCase() === "nan") {
        const vals = Object.values(row).map(v => String(v || '').trim()).filter(v => v.length > 2 && v.toLowerCase() !== 'nan');
        const partCand = vals.find(v => /^[A-Z0-9\\-\\.\\/]{4,30}$/i.test(v) && /\\d/.test(v));
        if (partCand) partNo = partCand;
      }"""

    if old_row_fallback in de_text:
        de_text = de_text.replace(old_row_fallback, new_row_fallback)
        print("Updated robust row fallback in processSalesUpload in js/data-engine.js")

    with open('js/data-engine.js', 'w', encoding='utf-8') as f:
        f.write(de_text)

    # 2. Update server.py
    with open('server.py', 'r', encoding='utf-8') as f:
        server_text = f.read()

    old_srv_kw = "['partno', 'partnumber', 'itemdesc', 'itemdescription', 'itemcode', 'itemname', 'description', 'partdescription', 'itemdesc']"
    new_srv_kw = "['itemcode_rev', 'itemcode', 'itemname', 'partno', 'partnumber', 'itemdesc', 'itemdescription', 'description', 'partdescription']"

    if old_srv_kw in server_text:
        server_text = server_text.replace(old_srv_kw, new_srv_kw)
        with open('server.py', 'w', encoding='utf-8') as f:
            f.write(server_text)
        print("Updated server.py header keywords")

    print("Final extractor fix script executed successfully.")

if __name__ == '__main__':
    apply_final_extractor_fix()
