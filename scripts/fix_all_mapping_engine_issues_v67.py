import re, os

print("=== Fixing DataEngine and Mapping Portal Column Inspection and Rules (v67) ===")

# 1. Update js/data-engine.js
data_engine_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\data-engine.js"
with open(data_engine_path, "r", encoding="utf-8") as f:
    js_content = f.read()

new_inspect_code = r"""  inspectColumnsByContent(rawRows) {
    if (!Array.isArray(rawRows) || rawRows.length === 0) return { partCol: null, descCol: null, brandCol: null };
    const sample = rawRows.slice(0, 20);
    const keys = Object.keys(sample[0]);

    let partCol = null;
    let descCol = null;
    let brandCol = null;

    // Check for exact / normalized key matches first
    for (let k of keys) {
      const kNorm = k.toLowerCase().replace(/[^a-z0-9]/g, '');
      if (!descCol && (kNorm.includes('itemname') || kNorm.includes('itemdescription') || kNorm.includes('partdescription') || kNorm.includes('description') || kNorm.includes('itemdesc') || kNorm.includes('desc') || kNorm.includes('title') || kNorm.includes('detail') || kNorm.includes('specification'))) {
        descCol = k;
      }
      if (!partCol && (kNorm.includes('itemcode') || kNorm.includes('partnumber') || kNorm.includes('partno') || kNorm.includes('itemcoderev') || kNorm.includes('partcode') || kNorm.includes('sku') || kNorm.includes('manpart') || kNorm.includes('material') || kNorm === 'part')) {
        partCol = k;
      }
      if (!brandCol && (kNorm.includes('brand') || kNorm.includes('make') || kNorm.includes('vendor') || kNorm.includes('oem') || kNorm.includes('manufacturer'))) {
        brandCol = k;
      }
    }

    // Phase 2: Content inspection if column names did not match
    if (!partCol || !descCol) {
      for (let k of keys) {
        if (k === brandCol) continue;
        const vals = sample.map(r => String(r[k] || '').trim()).filter(v => v.length > 0 && v.toLowerCase() !== 'nan');
        if (vals.length === 0) continue;

        const spaceRatio = vals.filter(v => v.includes(' ') || v.length > 12).length / vals.length;
        const codeRatio = vals.filter(v => /^[A-Z0-9\-\.\/]{4,30}$/i.test(v) && /\d/.test(v)).length / vals.length;

        if (!descCol && spaceRatio > 0.4 && k !== partCol) {
          descCol = k;
        } else if (!partCol && codeRatio > 0.4 && k !== descCol) {
          partCol = k;
        }
      }
    }

    return { partCol, descCol, brandCol };
  },"""

# Use string replace for safety
start_idx = js_content.find("inspectColumnsByContent(rawRows) {")
if start_idx != -1:
    end_idx = js_content.find("},", start_idx)
    if end_idx != -1:
        js_content = js_content[:start_idx] + new_inspect_code[2:] + js_content[end_idx+2:]
        print("Successfully replaced inspectColumnsByContent in js/data-engine.js")

with open(data_engine_path, "w", encoding="utf-8") as f:
    f.write(js_content)


# 2. Update js/mapping-portal.js fallback mapping logic
mapping_portal_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\mapping-portal.js"
with open(mapping_portal_path, "r", encoding="utf-8") as f:
    mp_content = f.read()

new_fallback_block = r"""      if (!mapped || mapped.length === 0) {
        console.log("Applying DataEngine domain mapping rules to all rows...");
        
        let detectedPartCol = null;
        let detectedDescCol = null;
        let detectedBrandCol = null;

        if (rawRows.length > 0) {
          const keys = Object.keys(rawRows[0]);
          for (let k of keys) {
            const kNorm = k.toLowerCase().replace(/[^a-z0-9]/g, '');
            if (!detectedDescCol && (kNorm.includes('itemname') || kNorm.includes('itemdescription') || kNorm.includes('partdescription') || kNorm.includes('description') || kNorm.includes('itemdesc') || kNorm.includes('desc') || kNorm.includes('title'))) {
              detectedDescCol = k;
            }
            if (!detectedPartCol && (kNorm.includes('itemcode') || kNorm.includes('partnumber') || kNorm.includes('partno') || kNorm.includes('itemcoderev') || kNorm.includes('partcode') || kNorm.includes('sku') || kNorm.includes('manpart') || kNorm === 'part')) {
              detectedPartCol = k;
            }
            if (!detectedBrandCol && (kNorm.includes('brand') || kNorm.includes('make') || kNorm.includes('vendor') || kNorm.includes('oem'))) {
              detectedBrandCol = k;
            }
          }
        }

        mapped = rawRows.map((row, idx) => {
          let partNo = detectedPartCol ? String(row[detectedPartCol] || '') : "";
          let desc = detectedDescCol ? String(row[detectedDescCol] || '') : "";
          let brand = detectedBrandCol ? String(row[detectedBrandCol] || '') : "";

          if (!partNo) partNo = String(row.partNo || row['Part No'] || row['ItemCode'] || row['ManPart'] || Object.values(row)[0] || `PART-${idx+1}`).trim();
          if (!desc) desc = String(row.description || row.desc || row['Description'] || row['ItemDesc'] || Object.values(row)[1] || '').trim();
          if (!brand) brand = String(row.brand || row['Brand'] || row['BRAND'] || 'GENERIC').trim();

          const qty = parseFloat(row.qty || row['Qty'] || 1) || 1;
          const unitPrice = parseFloat(row.price || row['Price'] || row['UnitCost'] || 250) || 250;

          const m = (window.DataEngine && typeof window.DataEngine.mapRow === 'function')
            ? window.DataEngine.mapRow(partNo, desc, brand)
            : this.applyInlineDomainRules(partNo, desc, brand);

          return {
            id: `MAP-${idx + 1001}`,
            partNo: partNo,
            description: desc,
            brand: brand || m.make || 'GENERIC',
            aggregate: m.aggregate || "CHILD PARTS",
            subAggregate: m.subAggregate || "GENERAL",
            component: m.component || "BOLT",
            category: m.category || "Mechanical Parts",
            qty: qty,
            unitPrice: unitPrice,
            totalSales: qty * unitPrice,
            confidence: m.confidence || "HIGH",
            confidenceScore: m.confidenceScore || 95,
            matchMethod: m.matchMethod || "HEURISTIC_DOMAIN_RULE",
            remarks: m.remarks || "Auto Mapped (Domain Rule)",
            isEdited: false,
            ...row
          };
        });
      }"""

fb_start = mp_content.find("if (!mapped || mapped.length === 0) {")
if fb_start != -1:
    fb_end = mp_content.find("if (window.DataEngine) {", fb_start)
    if fb_end != -1:
        mp_content = mp_content[:fb_start] + new_fallback_block + "\n\n      " + mp_content[fb_end:]
        print("Successfully replaced fallback mapping block in js/mapping-portal.js")

with open(mapping_portal_path, "w", encoding="utf-8") as f:
    f.write(mp_content)

print("Done updating DataEngine and Mapping Portal JS files!")
