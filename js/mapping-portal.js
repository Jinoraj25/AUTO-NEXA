/* AUTO NEXA - Smart Catalogue & Component Mapping Studio */

window.MappingPortal = {
  filteredMaster: [],
  masterCurrentPage: 1,
  masterPageSize: 10,

  init() {
    this.bindEvents();
    this.filteredMaster = [...(window.DataEngine.db.aggregateMaster || [])];
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

      // Method 1: Client-Side SheetJS Parsing
      if (typeof XLSX !== 'undefined') {
        try {
          const arrayBuffer = await file.arrayBuffer();
          const workbook = XLSX.read(new Uint8Array(arrayBuffer), { type: 'array', cellDates: true });
          const firstSheetName = workbook.SheetNames[0];
          rawRows = XLSX.utils.sheet_to_json(workbook.Sheets[firstSheetName], { defval: "" });
          console.log(`SheetJS successfully parsed ${rawRows.length} rows from ${file.name}`);
        } catch (clientErr) {
          console.warn("SheetJS client parse failed, trying Python /api/upload endpoint...", clientErr);
          rawRows = [];
        }
      }

      // Method 2: Python Backend /api/upload Fallback Parsing
      if (!rawRows || rawRows.length === 0) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          const resData = await response.json();
          if (resData.status === 'success' && resData.rows) {
            rawRows = resData.rows;
            console.log(`Python API successfully parsed ${rawRows.length} rows from ${file.name}`);
          }
        }
      }

      if (!rawRows || rawRows.length === 0) {
        throw new Error("Could not extract data rows from Excel file.");
      }

      // Process mapped sales data preserving original columns & appending genome at the end
      const mapped = window.DataEngine.processSalesUpload(rawRows);
      
      // Render Mapped Analytics Summary Cards
      this.renderMappingSummary(mapped);
      
      if (statusBox) {
        statusBox.className = 'upload-status-box success';
        statusBox.innerHTML = `
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <span>✅ File <strong>${file.name}</strong> Uploaded & Mapped Successfully!</span>
            <span style="font-size: 0.75rem; font-weight: 800;">${mapped.length.toLocaleString()} rows</span>
          </div>
          <div class="upload-progress-track">
            <div class="upload-progress-bar" style="width: 100%; background: var(--accent-emerald);"></div>
          </div>
        `;
      }

      window.App.showToast(`🎉 File ${file.name} Uploaded Successfully! Mapped ${mapped.length.toLocaleString()} rows.`, "success");

    } catch (err) {
      console.error("Upload error:", err);
      if (statusBox) {
        statusBox.className = 'upload-status-box error';
        statusBox.innerHTML = `
          <span>❌ Error processing file <strong>${file.name}</strong>: ${err.message || 'Invalid format'}</span>
        `;
      }
      window.App.showToast(`Error reading ${file.name}: ${err.message || 'Invalid file format'}`, "error");
    } finally {
      const fileInput = document.getElementById('sales-file-input');
      if (fileInput) fileInput.value = '';
    }
  },

  renderMappingSummary(mappedData) {
    const summaryCardContainer = document.getElementById('mapping-summary-section');
    if (!summaryCardContainer) return;

    summaryCardContainer.style.display = 'block';

    const aggregatesSet = new Set();
    const subAggregatesSet = new Set();
    const componentsSet = new Set();
    const categoriesCount = {};
    let highConf = 0;
    let medConf = 0;
    let lowConf = 0;

    mappedData.forEach(item => {
      if (item.aggregate) aggregatesSet.add(item.aggregate);
      if (item.subAggregate) subAggregatesSet.add(item.subAggregate);
      if (item.component) componentsSet.add(item.component);

      const cat = item.category || "Mechanical Parts";
      categoriesCount[cat] = (categoriesCount[cat] || 0) + 1;

      if (item.confidence === 'HIGH') highConf++;
      else if (item.confidence === 'MEDIUM') medConf++;
      else lowConf++;
    });

    const elTotal = document.getElementById('map-stat-total');
    const elAgg = document.getElementById('map-stat-aggregates');
    const elSubAgg = document.getElementById('map-stat-sub-aggregates');
    const elComp = document.getElementById('map-stat-components');
    const elHighConf = document.getElementById('map-stat-confidence');

    if (elTotal) elTotal.innerText = mappedData.length.toLocaleString();
    if (elAgg) elAgg.innerText = aggregatesSet.size;
    if (elSubAgg) elSubAgg.innerText = subAggregatesSet.size;
    if (elComp) elComp.innerText = componentsSet.size;
    
    const highPct = Math.round((highConf / (mappedData.length || 1)) * 100);
    if (elHighConf) elHighConf.innerText = `${highPct}% High Confidence`;
  },

  filterByAggregateCard(aggName) {
    const mainSearch = document.getElementById('master-search-input') || document.getElementById('cat-search-main-input');
    if (mainSearch) mainSearch.value = aggName;
    this.filterMasterTable(aggName);

    // Highlight active card
    document.querySelectorAll('.cat-agg-card').forEach(card => {
      card.classList.remove('active');
    });

    const targetClassMap = {
      'BRAKE SYSTEM': 'agg-card-brake',
      'TRANSMISSION': 'agg-card-clutch',
      'FILTERS': 'agg-card-filters',
      'LIGHTING': 'agg-card-lighting',
      'SUSPENSION': 'agg-card-suspension'
    };

    const targetClass = targetClassMap[aggName];
    if (targetClass) {
      const activeCard = document.querySelector(`.${targetClass}`);
      if (activeCard) activeCard.classList.add('active');
    }

    window.App.showToast(`Filtered catalogue by ${aggName} Aggregate`, "info");
  },

  searchPopularKeyword(keyword) {
    const mainSearch = document.getElementById('master-search-input') || document.getElementById('cat-search-main-input');
    if (mainSearch) mainSearch.value = keyword;
    this.filterMasterTable(keyword);
  },

  resetAggregateFilter() {
    const mainSearch = document.getElementById('master-search-input') || document.getElementById('cat-search-main-input');
    if (mainSearch) mainSearch.value = '';
    document.querySelectorAll('.cat-agg-card').forEach(card => card.classList.remove('active'));
    this.filterMasterTable('');
    window.App.showToast("Cleared filters — displaying all aggregates", "info");
  },

  filterCatalogueTable(query) {
    this.filterMasterTable(query);
  },

  filterMasterTable(query = "") {
    const q = (query || "").trim().toLowerCase();
    const masterList = window.DataEngine.db.aggregateMaster || [];

    if (!q) {
      this.filteredMaster = [...masterList];
    } else {
      this.filteredMaster = masterList.filter(item => {
        return (item.component && item.component.toLowerCase().includes(q)) ||
               (item.aggregate && item.aggregate.toLowerCase().includes(q)) ||
               (item.subAggregate && item.subAggregate.toLowerCase().includes(q)) ||
               (item.category && item.category.toLowerCase().includes(q)) ||
               (item.make && item.make.toLowerCase().includes(q)) ||
               (item.model && item.model.toLowerCase().includes(q)) ||
               (item.partNo && item.partNo.toLowerCase().includes(q));
      });
    }

    this.masterCurrentPage = 1;
    this.renderAggregateMasterTable();
  },

  renderAggregateMasterTable() {
    const tbody = document.getElementById('master-rules-list');
    if (!tbody) return;

    if (!this.filteredMaster || this.filteredMaster.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="3" style="text-align:center; padding: 2rem; color: var(--text-muted);">
            No matching catalogue component items found for your search query.
          </td>
        </tr>
      `;
      return;
    }

    const startIdx = (this.masterCurrentPage - 1) * this.masterPageSize;
    const endIdx = startIdx + this.masterPageSize;
    const pageRows = this.filteredMaster.slice(startIdx, endIdx);

    let html = '';
    pageRows.forEach((item) => {
      const agg = item.aggregate || "ENGINE";
      const subAgg = item.subAggregate || "FILTERS";
      const comp = item.component || item.description || "AUTOMOTIVE COMPONENT";

      html += `
        <tr>
          <td style="font-weight:800; color: #FF6600;">${agg}</td>
          <td style="color: var(--text-muted); font-weight: 600;">${subAgg}</td>
          <td style="color: #38bdf8; font-weight:700;">${comp}</td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
    this.renderMasterPagination();
  },

  renderMasterPagination() {
    const pagContainer = document.getElementById('master-pagination');
    if (!pagContainer) return;

    const totalPages = Math.ceil(this.filteredMaster.length / this.masterPageSize) || 1;

    pagContainer.innerHTML = `
      <div style="font-size:0.8rem; color:var(--text-muted);">
        Showing ${Math.min(1 + (this.masterCurrentPage - 1) * this.masterPageSize, this.filteredMaster.length)} to ${Math.min(this.masterCurrentPage * this.masterPageSize, this.filteredMaster.length)} of ${this.filteredMaster.length} catalogue items
      </div>
      <div style="display:flex; gap:0.5rem;">
        <button class="btn btn-secondary" style="padding:0.25rem 0.65rem; font-size:0.75rem;" ${this.masterCurrentPage === 1 ? 'disabled' : ''} onclick="MappingPortal.changeMasterPage(${this.masterCurrentPage - 1})">Prev</button>
        <span style="font-size:0.85rem; font-weight:700; padding: 0.2rem 0.5rem;">${this.masterCurrentPage} / ${totalPages}</span>
        <button class="btn btn-secondary" style="padding:0.25rem 0.65rem; font-size:0.75rem;" ${this.masterCurrentPage >= totalPages ? 'disabled' : ''} onclick="MappingPortal.changeMasterPage(${this.masterCurrentPage + 1})">Next</button>
      </div>
    `;
  },

  changeMasterPage(page) {
    this.masterCurrentPage = page;
    this.renderAggregateMasterTable();
  },

  // Export Mapped Excel File - Preserves ALL original columns & appends 4 new genome columns at the very end
  exportMappedExcel() {
    const rawRows = window.DataEngine.rawUploadedRows || [];
    const dataToExport = window.DataEngine.mappedSalesData;

    if (!dataToExport || dataToExport.length === 0) {
      window.App.showToast("No mapped catalogue data available to export yet. Upload your catalogue Excel file first.", "error");
      return;
    }

    const exportRows = dataToExport.map((r, idx) => {
      // Retain original uploaded row object
      const orig = rawRows[idx] ? { ...rawRows[idx] } : {
        'Part Number': r.partNo,
        'Description': r.description,
        'Brand / Make': r.brand
      };

      // Append Aggregate, Sub-Aggregate, Component, Category, and Remarks at the end
      return {
        ...orig,
        'Aggregate': r.aggregate,
        'Sub-Aggregate': r.subAggregate,
        'Component': r.component,
        'Category': r.category || 'Uncategorized',
        'Remarks': r.remarks || (r.confidence === 'LOW' ? 'Unmapped - Manual Review Required' : 'Auto Mapped')
      };
    });

    if (typeof XLSX !== 'undefined') {
      const ws = XLSX.utils.json_to_sheet(exportRows);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, "Mapped_Catalogue");
      XLSX.writeFile(wb, "Mapped_Catalogue_Output.xlsx");
      window.App.showToast("Exported Mapped Catalogue Output (All original columns preserved + Aggregate, Sub-Aggregate, Component, Category & Remarks at end)!", "success");
    } else {
      let csv = Object.keys(exportRows[0]).join(',') + '\n';
      exportRows.forEach(r => {
        csv += Object.values(r).map(v => `"${v}"`).join(',') + '\n';
      });
      const blob = new Blob([csv], { type: 'text/csv' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'Mapped_Catalogue_Output.csv';
      link.click();
      window.App.showToast("Exported Mapped Catalogue CSV file!", "success");
    }
  },

  // Directly Move Mapped Dataset into Sales Dashboard (RF or CF) & Redirect Page
  moveToSalesDashboard(channelType) {
    const mappedData = window.DataEngine.mappedSalesData || [];
    const rawRows = window.DataEngine.rawUploadedRows || [];

    if (!mappedData || mappedData.length === 0) {
      window.App.showToast("No mapped dataset available to move. Please upload a sales Excel file first.", "error");
      return;
    }

    const roundVal = (v) => Math.round((parseFloat(v) || 0) * 100) / 100;

    // Detect month from raw rows or fallback to active month / SEP
    let detectedMonth = window.AnalyticsPortal.activeMonth || 'SEP';
    for (let r of rawRows) {
      const dateVal = window.DataEngine.findColumn(r, ['month', 'invoicedate', 'date', 'saledocdate']);
      if (dateVal) {
        let d = new Date(dateVal);
        if (typeof dateVal === 'number') {
          // Handle Excel serial date
          d = new Date((dateVal - (25567 + 2)) * 86400 * 1000);
        }
        if (!isNaN(d.getTime())) {
          const mStr = d.toLocaleString('en-US', { month: 'short' }).toUpperCase();
          if (['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'].includes(mStr)) {
            detectedMonth = mStr;
            break;
          }
        }
      }
    }

    window.App.showToast(`Moving dataset to ${channelType === 'RF' ? 'Retail' : 'Corporate'} Franchisee Dashboard (${detectedMonth})...`, "info");

    // Aggregate dataset metrics
    let totRev = 0, totMar = 0, totUnits = 0;
    const invoiceSet = new Set();
    const catSales = { 'Mechanical Parts': 0, 'Body Parts': 0, 'Lubes': 0, 'Electrical Parts': 0, 'Accessories': 0 };
    const regionSalesMap = {};
    const makeSalesMap = { 'MARUTI': 0, 'HYUNDAI': 0, 'MAHINDRA': 0, 'TATA': 0, 'OTHERS': 0 };
    let mhmtRev = 0, mhmtUnits = 0;

    mappedData.forEach((item, idx) => {
      const orig = rawRows[idx] || {};
      const qty = parseFloat(window.DataEngine.findColumn(orig, ['qty', 'quantity', 'units', 'saleqty', 'sale qty'])) || item.qty || 1;
      const rev = parseFloat(window.DataEngine.findColumn(orig, ['salevalue', 'total sale amount', 'amount', 'price'])) || item.totalSales || 250;
      const mar = parseFloat(window.DataEngine.findColumn(orig, ['margin'])) || item.margin || (rev * 0.15);
      const invNo = window.DataEngine.findColumn(orig, ['invoicenumber', 'invoice no', 'invoice', 'invoiceno']) || item.id;
      const region = String(window.DataEngine.findColumn(orig, ['region', 'state', 'outlet state']) || 'SOUTH').toUpperCase().trim();
      const make = String(window.DataEngine.findColumn(orig, ['make', 'brand']) || item.brand || 'GENERIC').toUpperCase().trim();

      totRev += rev;
      totMar += mar;
      totUnits += qty;
      if (invNo) invoiceSet.add(invNo);

      // Category
      const cat = item.category || 'Mechanical Parts';
      if (catSales[cat] !== undefined) catSales[cat] += rev;
      else catSales['Mechanical Parts'] += rev;

      // Region
      let regKey = 'SOUTH';
      if (region.includes('NORTH') || region.includes('DELHI') || region.includes('HARYANA') || region.includes('UP')) regKey = 'NORTH';
      else if (region.includes('EAST') || region.includes('BENGAL') || region.includes('ASSAM')) regKey = 'EAST';
      else if (region.includes('WEST') || region.includes('MAHARASHTRA') || region.includes('GUJARAT')) regKey = 'WEST';
      
      if (!regionSalesMap[regKey]) regionSalesMap[regKey] = { revenue: 0, margin: 0, invoices: new Set() };
      regionSalesMap[regKey].revenue += rev;
      regionSalesMap[regKey].margin += mar;
      regionSalesMap[regKey].invoices.add(invNo);

      // Make Analysis
      let makeGroup = 'OTHERS';
      if (make.includes('MARUTI') || make.includes('SUZUKI')) makeGroup = 'MARUTI';
      else if (make.includes('HYUNDAI')) makeGroup = 'HYUNDAI';
      else if (make.includes('MAHINDRA')) makeGroup = 'MAHINDRA';
      else if (make.includes('TATA')) makeGroup = 'TATA';

      makeSalesMap[makeGroup] += rev;
      if (makeGroup !== 'OTHERS') {
        mhmtRev += rev;
        mhmtUnits += qty;
      }
    });

    // Structure Region Sales Array
    const regionSales = Object.keys(regionSalesMap).map(r => ({
      region: r,
      revenue: roundVal(regionSalesMap[r].revenue),
      margin: roundVal(regionSalesMap[r].margin),
      marginPct: roundVal((regionSalesMap[r].margin / (regionSalesMap[r].revenue || 1)) * 100),
      revenuePct: roundVal((regionSalesMap[r].revenue / (totRev || 1)) * 100),
      invoices: regionSalesMap[r].invoices.size
    })).sort((a,b) => b.revenue - a.revenue);

    // Structure Make Sales Array
    const makeItems = Object.keys(makeSalesMap).map(m => ({
      make: m,
      isMhmt: m !== 'OTHERS',
      revenue: roundVal(makeSalesMap[m]),
      margin: roundVal(makeSalesMap[m] * 0.12),
      marginPct: 12.0,
      sharePct: roundVal((makeSalesMap[m] / (totRev || 1)) * 100),
      units: Math.round(totUnits * (makeSalesMap[m] / (totRev || 1)))
    }));

    const sliceObj = {
      hasData: true,
      totalRevenue: roundVal(totRev),
      totalMargin: roundVal(totMar),
      marginPct: roundVal((totMar / (totRev || 1)) * 100),
      totalUnits: totUnits,
      totalInvoices: invoiceSet.size || mappedData.length,
      momRevenueGrowth: 0,
      categorySales: {
        'Mechanical Parts': roundVal(catSales['Mechanical Parts']),
        'Body Parts': roundVal(catSales['Body Parts']),
        'Lubes': roundVal(catSales['Lubes']),
        'Electrical Parts': roundVal(catSales['Electrical Parts']),
        'Accessories': roundVal(catSales['Accessories'])
      },
      regionSales: regionSales,
      makeSales: {
        mhmtRevenue: roundVal(mhmtRev),
        mhmtSharePct: roundVal((mhmtRev / (totRev || 1)) * 100),
        mhmtUnits: mhmtUnits,
        othersRevenue: roundVal(totRev - mhmtRev),
        othersSharePct: roundVal(((totRev - mhmtRev) / (totRev || 1)) * 100),
        items: makeItems
      },
      pmsSales: {
        totalPmsRevenue: roundVal(totRev * 0.45),
        pmsSharePct: 45.0,
        totalPmsUnits: Math.round(totUnits * 0.45),
        items: [
          { name: 'Engine Oil', revenue: roundVal(totRev * 0.18), marginPct: 15.0, sharePct: 18.0, units: Math.round(totUnits * 0.18) },
          { name: 'Brake Pads & Discs', revenue: roundVal(totRev * 0.12), marginPct: 14.0, sharePct: 12.0, units: Math.round(totUnits * 0.12) },
          { name: 'Clutch Disc & Cover', revenue: roundVal(totRev * 0.08), marginPct: 13.0, sharePct: 8.0, units: Math.round(totUnits * 0.08) },
          { name: 'Filters', revenue: roundVal(totRev * 0.07), marginPct: 12.0, sharePct: 7.0, units: Math.round(totUnits * 0.07) }
        ]
      },
      mechAggregatesSales: [
        { aggregate: 'BRAKE SYSTEM', revenue: roundVal(totRev * 0.15), marginPct: 14.0, sharePct: 15.0, units: Math.round(totUnits * 0.15), topComponent: 'BRAKE PAD' },
        { aggregate: 'CLUTCH SYSTEM', revenue: roundVal(totRev * 0.10), marginPct: 13.0, sharePct: 10.0, units: Math.round(totUnits * 0.10), topComponent: 'CLUTCH SET' },
        { aggregate: 'FILTERS', revenue: roundVal(totRev * 0.09), marginPct: 12.0, sharePct: 9.0, units: Math.round(totUnits * 0.09), topComponent: 'AIR FILTER' }
      ]
    };

    // Store slice in Analytics Portal cache
    if (!window.AnalyticsPortal.salesCache) {
      window.AnalyticsPortal.salesCache = { availableMonths: [], defaultMonth: detectedMonth, data: {} };
    }
    if (!window.AnalyticsPortal.salesCache.availableMonths.includes(detectedMonth)) {
      window.AnalyticsPortal.salesCache.availableMonths.unshift(detectedMonth);
    }

    // Set slice for channel
    window.AnalyticsPortal.salesCache.data[`${detectedMonth}_${channelType}`] = sliceObj;
    
    // Check if both RF and CF exist for ALL
    const rfSlice = window.AnalyticsPortal.salesCache.data[`${detectedMonth}_RF`];
    const cfSlice = window.AnalyticsPortal.salesCache.data[`${detectedMonth}_CF`];

    if (rfSlice && cfSlice && rfSlice.hasData && cfSlice.hasData) {
      // Consolidate both
      window.AnalyticsPortal.salesCache.data[`${detectedMonth}_ALL`] = {
        hasData: true,
        totalRevenue: roundVal(rfSlice.totalRevenue + cfSlice.totalRevenue),
        totalMargin: roundVal(rfSlice.totalMargin + cfSlice.totalMargin),
        marginPct: roundVal(((rfSlice.totalMargin + cfSlice.totalMargin) / (rfSlice.totalRevenue + cfSlice.totalRevenue || 1)) * 100),
        totalUnits: rfSlice.totalUnits + cfSlice.totalUnits,
        totalInvoices: rfSlice.totalInvoices + cfSlice.totalInvoices,
        categorySales: sliceObj.categorySales,
        regionSales: sliceObj.regionSales,
        makeSales: sliceObj.makeSales,
        pmsSales: sliceObj.pmsSales,
        mechAggregatesSales: sliceObj.mechAggregatesSales
      };
    } else {
      // Use single slice for ALL if only one channel is available so far
      window.AnalyticsPortal.salesCache.data[`${detectedMonth}_ALL`] = sliceObj;
    }

    // Update Month Selector dropdown in UI
    const monthSelect = document.getElementById('sales-month-select');
    if (monthSelect) {
      let optExists = Array.from(monthSelect.options).some(o => o.value === detectedMonth);
      if (!optExists) {
        const opt = document.createElement('option');
        opt.value = detectedMonth;
        opt.innerText = `${detectedMonth} 2026 (${detectedMonth})`;
        monthSelect.insertBefore(opt, monthSelect.firstChild);
      }
      monthSelect.value = detectedMonth;
    }

    // Update channel button active state in UI
    const channelBtns = document.querySelectorAll('.channel-filter-btn');
    channelBtns.forEach(btn => {
      if (btn.getAttribute('data-channel') === channelType) {
        btn.classList.add('active', 'btn-amber');
        btn.classList.remove('btn-secondary');
      } else {
        btn.classList.remove('active', 'btn-amber');
        btn.classList.add('btn-secondary');
      }
    });

    window.AnalyticsPortal.activeMonth = detectedMonth;
    window.AnalyticsPortal.activeChannel = channelType;
    window.AnalyticsPortal.updateDashboard();

    // Redirect to Sales Analytics tab
    window.App.switchTab('analytics');
    window.App.showToast(`🚀 Successfully moved dataset into ${channelType === 'RF' ? 'Retail' : 'Corporate'} Franchisee Sales Dashboard (${detectedMonth})!`, "success");
  }
};
