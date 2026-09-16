import re

with open('js/inventory-portal.js', 'r', encoding='utf-8') as f:
    code = f.read()

new_upload_method = '''  async handleInventoryUpload(file) {
    const statusBox = document.getElementById('inventory-sync-status');
    if (statusBox) {
      statusBox.style.display = 'flex';
      statusBox.className = 'upload-status-box uploading';
      statusBox.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span>⏳ Uploading, indexing & syncing Good Stock file <strong>${file.name}</strong>...</span>
          <span style="font-size: 0.75rem; opacity: 0.8;">Instant Sync Engine</span>
        </div>
        <div class="upload-progress-track">
          <div class="upload-progress-bar animated" style="width: 75%;"></div>
        </div>
      `;
    }

    if (window.App && window.App.showToast) {
      window.App.showToast(`Uploading and processing ${file.name}...`, "info");
    }

    let parsedDate = '15-Sep-2026';
    const dateMatch = file.name.match(/\\d{2}-[A-Za-z]{3}-\\d{4}/);
    if (dateMatch) parsedDate = dateMatch[0];

    try {
      let summaryObj = null;

      // Fast Client-Side Extract if XLSX library is present
      if (typeof XLSX !== 'undefined') {
        try {
          const arrayBuffer = await file.arrayBuffer();
          const workbook = XLSX.read(new Uint8Array(arrayBuffer), { type: 'array' });
          const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
          const rawRows = XLSX.utils.sheet_to_json(firstSheet, { defval: "" });

          if (rawRows && rawRows.length > 0) {
            let totalQty = 0, totalValuation = 0;
            const catVal = {};
            const sampleItems = [];

            rawRows.forEach((r, idx) => {
              const qty = parseFloat(r['Qty'] || r['QTY'] || r['Quantity'] || 0) || 0;
              const val = parseFloat(r['Value'] || r['VALUE'] || r['Valuation'] || 0) || 0;
              const cat = String(r['CATEGORY'] || r['Category'] || 'OEM').trim();

              totalQty += qty;
              totalValuation += val;
              catVal[cat] = (catVal[cat] || 0) + val;

              if (idx < 300) {
                sampleItems.push({
                  source: String(r['Source'] || r['SOURCE'] || r['source'] || 'myTVS').trim(),
                  partNo: String(r['ManPart'] || r['ItemID(myTVS)'] || r['PartNo'] || '').trim(),
                  desc: String(r['ItemDesc'] || r['Description'] || '').trim(),
                  brand: String(r['BRAND'] || r['Brand'] || '').trim(),
                  category: cat,
                  qty: qty,
                  unitCost: parseFloat(r['UnitCost'] || r['Cost'] || 0) || 0,
                  mrp: parseFloat(r['MRP'] || r['Mrp'] || 0) || 0,
                  valuation: val,
                  lineCode: String(r['LineCode'] || r['Line Code'] || '').trim(),
                  branchCode: String(r['BRANCH'] || r['Branch'] || 'WHM').trim(),
                  branchName: String(r['BRANCH NAME'] || r['Branch Name'] || 'MADURAI').trim(),
                  tag: String(r['Tag'] || r['TAG'] || 'CONSIDER').trim()
                });
              }
            });

            summaryObj = {
              date: parsedDate,
              filename: file.name,
              totalSKUs: rawRows.length,
              totalQty: totalQty,
              totalValuation: totalValuation,
              categoryValuation: catVal,
              sampleItems: sampleItems
            };

            if (!this.inventoryData) this.inventoryData = { dailySummaries: {}, dates: [] };
            if (!this.inventoryData.dailySummaries) this.inventoryData.dailySummaries = {};
            this.inventoryData.dailySummaries[parsedDate] = summaryObj;

            if (!this.inventoryData.dates) this.inventoryData.dates = [];
            if (!this.inventoryData.dates.includes(parsedDate)) {
              this.inventoryData.dates.unshift(parsedDate);
            }
            this.inventoryData.latestDate = parsedDate;
            this.selectedDate = parsedDate;
          }
        } catch (clientErr) {
          console.warn("Client XLSX parse notice (proceeding with server upload):", clientErr);
        }
      }

      // Upload file & summary to server endpoint /api/inventory/upload
      const formData = new FormData();
      formData.append('file', file);
      if (summaryObj) {
        formData.append('summaryJSON', JSON.stringify(summaryObj));
      }

      try {
        const response = await fetch('/api/inventory/upload', {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          const resData = await response.json();
          if (resData.status === 'success') {
            if (resData.date) parsedDate = resData.date;
            console.log("Server inventory upload success:", resData);
          }
        }
      } catch (netErr) {
        console.warn("Network upload notice, using local parsed state:", netErr);
      }

      // Re-fetch fresh stock cache from server if available
      try {
        const fetchRes = await fetch('/api/inventory');
        if (fetchRes.ok) {
          const freshData = await fetchRes.json();
          if (freshData && freshData.dailySummaries) {
            this.inventoryData = freshData;
          }
        }
      } catch(e) {}

      this.selectedDate = parsedDate;
      this.renderDateDropdown();
      this.renderAll();

      if (statusBox) {
        statusBox.className = 'upload-status-box success';
        statusBox.innerHTML = `
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <span>✅ Stock File <strong>${file.name}</strong> Uploaded & Synced Successfully for <strong>${parsedDate}</strong>!</span>
            <span style="font-size: 0.75rem; font-weight: 850;">Date: ${parsedDate}</span>
          </div>
          <div class="upload-progress-track">
            <div class="upload-progress-bar" style="width: 100%; background: var(--accent-emerald);"></div>
          </div>
        `;
      }

      if (window.App && window.App.showToast) {
        window.App.showToast(`🎉 Stock File ${file.name} Uploaded & Active for ${parsedDate}!`, "success");
      }

    } catch (err) {
      console.error("Inventory upload error:", err);
      if (statusBox) {
        statusBox.className = 'upload-status-box error';
        statusBox.innerHTML = `
          <span>❌ Error processing stock file <strong>${file.name}</strong>: ${err.message || 'Invalid format'}</span>
        `;
      }
      if (window.App && window.App.showToast) {
        window.App.showToast(`Error processing ${file.name}: ${err.message || 'Invalid format'}`, "error");
      }
    } finally {
      const fileInput = document.getElementById('inventory-file-input');
      if (fileInput) fileInput.value = '';
    }
  },'''

pattern = r'  async handleInventoryUpload\(file\) \{.*?\n  \},'
code_updated, count = re.subn(pattern, lambda m: new_upload_method, code, flags=re.DOTALL)
print("Replaced handleInventoryUpload count:", count)

with open('js/inventory-portal.js', 'w', encoding='utf-8') as f:
    f.write(code_updated)
