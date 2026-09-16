import re

with open('js/mapping-portal.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Add DataEngine guard inside handleFileUpload
old_upload = '''      if (!rawRows || rawRows.length === 0) {
        throw new Error("Could not extract data rows from Excel file.");
      }

      // Process mapped sales data preserving original columns & appending genome at the end
      const mapped = window.DataEngine.processSalesUpload(rawRows);'''

new_upload = '''      if (!rawRows || rawRows.length === 0) {
        throw new Error("Could not extract data rows from Excel file.");
      }

      // Ensure DataEngine is attached & initialized
      if (!window.DataEngine || typeof window.DataEngine.processSalesUpload !== 'function') {
        if (window.DataEngine && typeof window.DataEngine.init === 'function') {
          window.DataEngine.init();
        }
      }
      if (!window.DataEngine || typeof window.DataEngine.processSalesUpload !== 'function') {
        throw new Error("DataEngine mapping algorithms are initializing. Please wait a moment and try again.");
      }

      // Process mapped sales data preserving original columns & appending genome at the end
      const mapped = window.DataEngine.processSalesUpload(rawRows);'''

code_updated = code.replace(old_upload, new_upload)

# Add handleMasterRulesUpload method to MappingPortal
master_upload_method = '''  async handleMasterRulesUpload(file) {
    if (!file) return;
    window.App.showToast(`Uploading Master Rules (${file.name})...`, "info");
    try {
      let rules = [];
      if (typeof XLSX !== 'undefined') {
        const arrayBuffer = await file.arrayBuffer();
        const wb = XLSX.read(new Uint8Array(arrayBuffer), { type: 'array' });
        const firstSheet = wb.Sheets[wb.SheetNames[0]];
        const rawRows = XLSX.utils.sheet_to_json(firstSheet, { defval: "" });
        
        rawRows.forEach(r => {
          const agg = String(r['AGGREGATE'] || r['Aggregate'] || r['aggregate'] || '').trim();
          const subAgg = String(r['SUB-AGGREGATE'] || r['Sub-Aggregate'] || r['SubAggregate'] || r['subAggregate'] || '').trim();
          const comp = String(r['COMPONENT'] || r['Component'] || r['component'] || '').trim();
          const cat = String(r['CATEGORY'] || r['Category'] || r['category'] || 'Mechanical Parts').trim();
          if (agg || subAgg || comp) {
            rules.append ? rules.push({ aggregate: agg, subAggregate: subAgg, component: comp, category: cat }) : null;
          }
        });
      }

      if (rules.length > 0) {
        if (window.DataEngine && window.DataEngine.db) {
          window.DataEngine.db.aggregateMaster = rules;
        }
        this.filteredMaster = [...rules];
        this.masterCurrentPage = 1;
        this.renderAggregateMasterTable();
        
        // Post to backend server API
        try {
          fetch('/api/master_rules/upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ aggregateMaster: rules })
          });
        } catch(e) {}

        window.App.showToast(`🎉 Updated Aggregate Master System with ${rules.length.toLocaleString()} rules!`, "success");
      } else {
        throw new Error("No valid rules found in Excel file.");
      }
    } catch(err) {
      console.error("Master rules upload error:", err);
      window.App.showToast(`Error updating Master Rules: ${err.message}`, "error");
    }
  },'''

# Insert before changeMasterPage
code_updated = code_updated.replace('  changeMasterPage(page) {', master_upload_method + '\n\n  changeMasterPage(page) {')

with open('js/mapping-portal.js', 'w', encoding='utf-8') as f:
    f.write(code_updated)

print("Updated js/mapping-portal.js with DataEngine guard and handleMasterRulesUpload!")
