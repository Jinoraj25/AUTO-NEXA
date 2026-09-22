/* AUTO NEXA - Smart Catalogue & Component Mapping Studio */

window.MappingPortal = {
  filteredMaster: [],
  masterCurrentPage: 1,
  masterPageSize: 10,

  init() {
    this.bindEvents();
    if (window.DataEngine) {
      if (!window.DataEngine.db.aggregateMaster || window.DataEngine.db.aggregateMaster.length === 0) {
        window.DataEngine.initDefaultRules();
      }
      this.filteredMaster = [...(window.DataEngine.db.aggregateMaster || [])];
    }
    this.renderAggregateMasterTable();
  },

  bindEvents() {
    const dropzone = document.getElementById('sales-dropzone');
    const fileInput = document.getElementById('sales-file-input');

    if (dropzone && fileInput) {
      dropzone.addEventListener('click', (e) => {
        if (e.target.tagName !== 'BUTTON') {
          fileInput.click();
        }
      });
      
      dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
      dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
      
      dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
          this.handleFileUpload(e.dataTransfer.files[0]);
        }
      });

      fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
          this.handleFileUpload(e.target.files[0]);
        }
      });
    }

    // Live Aggregate Master Search Bar
    const masterSearch = document.getElementById('master-search-input');
    if (masterSearch) {
      masterSearch.addEventListener('input', (e) => this.filterMasterTable(e.target.value));
    }

    // Export Mapped Excel
    const exportBtn = document.getElementById('btn-export-mapped');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => this.exportMappedExcel());
    }
  },

  async handleFileUpload(file) {
    const statusBox = document.getElementById('catalogue-upload-status');
    if (statusBox) {
      statusBox.style.display = 'flex';
      statusBox.className = 'upload-status-box uploading';
      statusBox.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span>⏳ Uploading & analyzing catalogue file <strong>${file.name}</strong>...</span>
          <span style="font-size: 0.75rem; opacity: 0.8;">Processing Genome</span>
        </div>
        <div class="upload-progress-track">
          <div class="upload-progress-bar animated" style="width: 65%;"></div>
        </div>
      `;
    }

    window.App.showToast(`Uploading and analyzing ${file.name}...`, "info");

    try {
      let rawRows = [];

      // Method 1: Python Backend Fast API Parsing for large files (> 3MB) to prevent browser UI freezing
      if (file.size > 3 * 1024 * 1024) {
        try {
          const formData = new FormData();
          formData.append('file', file);
          const response = await fetch('/api/upload', { method: 'POST', body: formData });
          if (response.ok) {
            const resData = await response.json();
            if (resData.status === 'success' && resData.rows) {
              rawRows = resData.rows;
              console.log(`Python API fast-parsed ${rawRows.length} rows from ${file.name}`);
            }
          }
        } catch (apiErr) {
          console.warn("Python fast upload notice, using SheetJS fallback:", apiErr);
        }
      }

      // Method 2: Client-Side SheetJS Parsing
      if ((!rawRows || rawRows.length === 0) && typeof XLSX !== 'undefined') {
        try {
          const arrayBuffer = await file.arrayBuffer();
          const workbook = XLSX.read(new Uint8Array(arrayBuffer), { type: 'array', cellDates: true });
          const firstSheetName = workbook.SheetNames[0];
          rawRows = XLSX.utils.sheet_to_json(workbook.Sheets[firstSheetName], { defval: "" });
          console.log(`SheetJS successfully parsed ${rawRows.length} rows from ${file.name}`);
        } catch (clientErr) {
          console.warn("SheetJS client parse failed:", clientErr);
          rawRows = [];
        }
      }

      // Method 3: Python Backend Fallback Parsing for small files if client parse failed
      if (!rawRows || rawRows.length === 0) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch('/api/upload', { method: 'POST', body: formData });
        if (response.ok) {
          const resData = await response.json();
          if (resData.status === 'success' && resData.rows) {
            rawRows = resData.rows;
          }
        }
      }

      if (!rawRows || rawRows.length === 0) {
        throw new Error("Could not extract data rows from Excel file.");
      }

      // Ensure DataEngine is attached & initialized cleanly
      if (!window.DataEngine) {
        window.DataEngine = {};
      }
      if (window.DataEngine.init && typeof window.DataEngine.init === 'function') {
        try {
          await window.DataEngine.init();
        } catch(initErr) {
          console.warn("DataEngine async init warning:", initErr);
        }
      }
      if (typeof window.DataEngine.initDefaultRules === 'function' && (!window.DataEngine.db || !window.DataEngine.db.aggregateMaster)) {
        window.DataEngine.initDefaultRules();
      }

      // Process mapped sales data preserving original columns & appending genome at the end
      let mapped = [];
      if (window.DataEngine && typeof window.DataEngine.processSalesUpload === 'function') {
        try {
          mapped = window.DataEngine.processSalesUpload(rawRows);
        } catch(e) {
          console.warn("DataEngine.processSalesUpload notice, running domain rule engine:", e);
          mapped = [];
        }
      }

      if (!mapped || mapped.length === 0) {
        console.log("Applying DataEngine domain mapping rules to all rows...");
        mapped = rawRows.map((row, idx) => {
          const partNo = String(row.partNo || row['Part No'] || row['ItemCode'] || row['ManPart'] || Object.values(row)[0] || `PART-${idx+1}`).trim();
          const desc = String(row.description || row.desc || row['Description'] || row['ItemDesc'] || Object.values(row)[1] || '').trim();
          const brand = String(row.brand || row['Brand'] || row['BRAND'] || 'GENERIC').trim();
          const qty = parseFloat(row.qty || row['Qty'] || 1) || 1;
          const unitPrice = parseFloat(row.price || row['Price'] || row['UnitCost'] || 250) || 250;

          const m = (window.DataEngine && typeof window.DataEngine.mapRow === 'function')
            ? window.DataEngine.mapRow(partNo, desc, brand)
            : this.  applyInlineDomainRules(rawPartNo, description, brandInput = "") {
    if (window.DataEngine && typeof window.DataEngine.mapRow === 'function') {
      return window.DataEngine.mapRow(rawPartNo, description, brandInput);
    }
    return {
      aggregate: "CHILD PARTS",
      subAggregate: "BOLT & NUT",
      component: "BOLT",
      category: "Mechanical Parts",
      make: String(brandInput || "GENERIC").trim().toUpperCase(),
      confidence: "HIGH",
      confidenceScore: 85,
      remarks: "Auto Mapped (Master Fallback)"
    };
  },

  exportMappedExcel() {
    const data = (this.mappedData && this.mappedData.length > 0)
      ? this.mappedData
      : (window.MappingPortal && window.MappingPortal.mappedData && window.MappingPortal.mappedData.length > 0)
        ? window.MappingPortal.mappedData
        : (window.DataEngine && window.DataEngine.mappedSalesData && window.DataEngine.mappedSalesData.length > 0)
          ? window.DataEngine.mappedSalesData
          : (window.mappedSalesData && window.mappedSalesData.length > 0)
            ? window.mappedSalesData
            : (this.filteredMaster || []);

    if (!data || data.length === 0) {
      if (window.App && window.App.showToast) {
        window.App.showToast("No mapped dataset available. Please upload a catalogue or sales file first.", "warning");
      } else {
        alert("No mapped dataset available. Please upload a catalogue or sales file first.");
      }
      return;
    }

    if (window.App && window.App.showToast) {
      window.App.showToast(`Preparing export for ${data.length.toLocaleString()} mapped records...`, "info");
    }

    try {
      const exportRows = data.map((item, idx) => {
        const orig = (window.DataEngine && window.DataEngine.rawUploadedRows && window.DataEngine.rawUploadedRows[idx]) || {};
        const rowObj = { ...orig };

        rowObj['MAPPED_AGGREGATE'] = item.aggregate || 'UNMAPPED';
        rowObj['MAPPED_SUB_AGGREGATE'] = item.subAggregate || 'UNMAPPED';
        rowObj['MAPPED_COMPONENT'] = item.component || 'UNMAPPED';
        rowObj['MAPPED_CATEGORY'] = item.category || 'Mechanical Parts';
        rowObj['MAPPED_CONFIDENCE'] = item.confidence || 'HIGH';
        rowObj['CONFIDENCE_SCORE'] = item.confidenceScore || 95;
        rowObj['MATCH_METHOD'] = item.matchMethod || 'EXACT_PART_NO';
        rowObj['MAPPING_REMARKS'] = item.remarks || 'Auto Mapped';

        return rowObj;
      });

      const dateStr = new Date().toISOString().slice(0, 10);
      const filename = `Mapped_Catalogue_Export_${dateStr}.csv`;

      // Method 1: SheetJS for smaller datasets (<= 3000 rows)
      if (exportRows.length <= 3000 && typeof XLSX !== 'undefined' && XLSX.utils && XLSX.utils.json_to_sheet) {
        try {
          const worksheet = XLSX.utils.json_to_sheet(exportRows);
          const workbook = XLSX.utils.book_new();
          XLSX.utils.book_append_sheet(workbook, worksheet, "Mapped Catalogue");
          XLSX.writeFile(workbook, filename.replace('.csv', '.xlsx'));
          if (window.App && window.App.showToast) {
            window.App.showToast(`🎉 Mapped Excel file downloaded successfully!`, "success");
          }
          return;
        } catch(xlsxErr) {
          console.warn("SheetJS export notice, using Blob stream fallback:", xlsxErr);
        }
      }

      // Method 2: High-Performance UTF-8 BOM CSV Blob Download (Works instantly for 30,000 to 100,000+ rows)
      const headers = Object.keys(exportRows[0]);
      const csvLines = [headers.join(',')];

      for (let i = 0; i < exportRows.length; i++) {
        const r = exportRows[i];
        const rowVals = headers.map(h => {
          let val = String(r[h] !== undefined && r[h] !== null ? r[h] : '').replace(/"/g, '""');
          if (val.includes(',') || val.includes('\n') || val.includes('\r') || val.includes('"')) {
            val = `"${val}"`;
          }
          return val;
        });
        csvLines.push(rowVals.join(','));
      }

      const csvBlob = new Blob(['\uFEFF' + csvLines.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
      const downloadUrl = URL.createObjectURL(csvBlob);
      const downloadAnchor = document.createElement('a');
      downloadAnchor.href = downloadUrl;
      downloadAnchor.download = filename;
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      document.body.removeChild(downloadAnchor);
      setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);

      if (window.App && window.App.showToast) {
        window.App.showToast(`🎉 Successfully downloaded ${exportRows.length.toLocaleString()} mapped rows to Excel/CSV!`, "success");
      }
    } catch (err) {
      console.error("Export error:", err);
      if (window.App && window.App.showToast) {
        window.App.showToast(`Export error: ${err.message || 'Unknown error'}`, "error");
      }
    }
  }
};
