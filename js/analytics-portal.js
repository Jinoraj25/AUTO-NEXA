/* AUTO NEXA - Sales Intelligence & Dark Store Analytics Portal (RF vs CF) */

window.AnalyticsPortal = {
  salesCache: null,
  rfSalesData: [],
  cfSalesData: [],
  activeMonth: 'AUG',
  activeChannel: 'RF', // Default active channel: Retail Franchisee (RF)
  charts: {},

  async init() {
    // Set Chart.js Global Defaults for Premium Dark Theme
    if (typeof Chart !== 'undefined') {
      Chart.defaults.color = '#94a3b8';
      Chart.defaults.font.family = "'Inter', 'system-ui', sans-serif";
      Chart.defaults.font.size = 12;
      Chart.defaults.plugins.legend.labels.usePointStyle = true;
      Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(10, 10, 15, 0.95)';
      Chart.defaults.plugins.tooltip.titleColor = '#f8fafc';
      Chart.defaults.plugins.tooltip.bodyColor = '#cbd5e1';
      Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.08)';
      Chart.defaults.plugins.tooltip.borderWidth = 1;
      Chart.defaults.plugins.tooltip.padding = 12;
      Chart.defaults.plugins.tooltip.cornerRadius = 10;
      Chart.defaults.plugins.tooltip.titleFont = { weight: '700', size: 13 };
      Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
    }
    this.bindEvents();
    await this.loadSalesCache();
  },

  bindEvents() {
    // Month Selector Dropdown
    const monthSelect = document.getElementById('sales-month-select');
    if (monthSelect) {
      monthSelect.addEventListener('change', (e) => {
        this.activeMonth = e.target.value;
        this.updateDashboard();
        window.App.showToast(`Switched Sales Dashboard to ${e.target.options[e.target.selectedIndex].text}`, "info");
      });
    }

    // Franchisee Channel Filter Tabs (ALL, RF, CF)
    const channelBtns = document.querySelectorAll('.channel-filter-btn');
    channelBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const channel = btn.getAttribute('data-channel');
        this.activeChannel = channel;

        channelBtns.forEach(b => {
          b.classList.remove('active', 'btn-amber');
          b.classList.add('btn-secondary');
        });
        btn.classList.remove('btn-secondary');
        btn.classList.add('active', 'btn-amber');

        this.updateDashboard();
        window.App.showToast(`Filtered Sales by ${btn.innerText}`, "info");
      });
    });

    // File Upload Handlers (RF & CF)
    const rfInput = document.getElementById('rf-sales-input');
    if (rfInput) {
      rfInput.addEventListener('change', (e) => {
        if (e.target.files.length) this.handleSalesUpload(e.target.files[0], 'RF');
      });
    }

    const cfInput = document.getElementById('cf-sales-input');
    if (cfInput) {
      cfInput.addEventListener('change', (e) => {
        if (e.target.files.length) this.handleSalesUpload(e.target.files[0], 'CF');
      });
    }
  },

  async loadSalesCache() {
    try {
      let res = await fetch('data/sales_cache.json');
      if (!res.ok) {
        res = await fetch('sales_cache.json');
      }
      if (res.ok) {
        this.salesCache = await res.json();
        this.activeMonth = this.salesCache.defaultMonth || 'AUG';

        const monthSelect = document.getElementById('sales-month-select');
        if (monthSelect) monthSelect.value = this.activeMonth;

        console.log(`AnalyticsPortal: Loaded sales cache for ${this.activeMonth}!`);
      }
    } catch (e) {
      console.warn("AnalyticsPortal fetch error, using live upload mode:", e);
    }
    this.updateDashboard();
  },

  async handleSalesUpload(file, channelType) {
    const statusBoxId = channelType === 'RF' ? 'rf-upload-status' : 'cf-upload-status';
    const statusBox = document.getElementById(statusBoxId);

    if (statusBox) {
      statusBox.style.display = 'flex';
      statusBox.className = 'upload-status-box uploading';
      statusBox.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <span>⏳ Uploading & parsing ${channelType === 'RF' ? 'Retail Franchisee (RF)' : 'Corporate Franchisee (CF)'} file <strong>${file.name}</strong>...</span>
          <span style="font-size: 0.75rem; opacity: 0.8;">Processing Sales Data</span>
        </div>
        <div class="upload-progress-track">
          <div class="upload-progress-bar animated" style="width: 65%;"></div>
        </div>
      `;
    }

    window.App.showToast(`Uploading ${channelType} Sales Report (${file.name})...`, "info");
    try {
      let rawRows = [];

      if (typeof XLSX !== 'undefined') {
        try {
          const arrayBuffer = await file.arrayBuffer();
          const workbook = XLSX.read(new Uint8Array(arrayBuffer), { type: 'array', cellDates: true });
          const firstSheet = workbook.SheetNames[0];
          rawRows = XLSX.utils.sheet_to_json(workbook.Sheets[firstSheet], { defval: "" });
        } catch (e) {
          console.warn("SheetJS upload failed, using /api/upload...", e);
        }
      }

      if (!rawRows || rawRows.length === 0) {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        if (res.ok) {
          const resData = await res.json();
          rawRows = resData.rows || [];
        }
      }

      if (!rawRows || rawRows.length === 0) {
        throw new Error("Could not extract rows from sales report file.");
      }

      const processed = rawRows.map((row, idx) => {
        const partNo = window.DataEngine.findColumn(row, ['part', 'itemcode', 'code', 'sku']) || `PART-${idx+1}`;
        const desc = window.DataEngine.findColumn(row, ['desc', 'name', 'title']) || "";
        const brand = window.DataEngine.findColumn(row, ['brand', 'make', 'segment']) || "GENERIC";
        const qty = parseFloat(window.DataEngine.findColumn(row, ['qty', 'quantity', 'count'])) || 1;
        const price = parseFloat(window.DataEngine.findColumn(row, ['price', 'rate', 'amount', 'salevalue'])) || 250;
        const margin = parseFloat(window.DataEngine.findColumn(row, ['margin'])) || price * 0.15;
        const vendor = window.DataEngine.findColumn(row, ['categoey', 'vendor', 'segment']) || "OEM";
        const region = window.DataEngine.findColumn(row, ['region', 'zone', 'area']) || "SOUTH";

        const mapped = window.DataEngine.mapRow(partNo, desc, brand);

        return {
          id: `${channelType}-${idx+1001}`,
          channel: channelType,
          partNo: partNo,
          description: desc,
          brand: brand || mapped.make,
          vendorSegment: vendor,
          region: region,
          aggregate: mapped.aggregate,
          subAggregate: mapped.subAggregate,
          component: mapped.component,
          category: mapped.category,
          remarks: mapped.remarks,
          qty: qty,
          unitPrice: price,
          totalSales: qty * price,
          margin: margin,
          marginPct: ((margin / (qty * price || 1)) * 100).toFixed(2)
        };
      });

      if (channelType === 'RF') {
        this.rfSalesData = processed;
      } else {
        this.cfSalesData = processed;
      }

      if (statusBox) {
        statusBox.className = 'upload-status-box success';
        statusBox.innerHTML = `
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <span>✅ File <strong>${file.name}</strong> Uploaded & Processed Successfully!</span>
            <span style="font-size: 0.75rem; font-weight: 800;">${processed.length.toLocaleString()} sales lines</span>
          </div>
          <div class="upload-progress-track">
            <div class="upload-progress-bar" style="width: 100%; background: var(--accent-emerald);"></div>
          </div>
        `;
      }

      window.App.showToast(`🎉 File ${file.name} Uploaded Successfully! Loaded ${processed.length.toLocaleString()} ${channelType === 'RF' ? 'Retail' : 'Corporate'} Franchisee sales lines.`, "success");
      this.updateDashboard();

    } catch (err) {
      console.error("Sales upload error:", err);
      if (statusBox) {
        statusBox.className = 'upload-status-box error';
        statusBox.innerHTML = `
          <span>❌ Error uploading ${file.name}: ${err.message || 'Parse error'}</span>
        `;
      }
      window.App.showToast(`Error parsing ${channelType} sales file: ${err.message}`, "error");
    }
  },

  updateDashboard() {
    const key = `${this.activeMonth}_${this.activeChannel}`;
    let sliceData = null;

    if (this.salesCache && this.salesCache.data && this.salesCache.data[key]) {
      sliceData = this.salesCache.data[key];
    } else if (this.salesCache && this.salesCache.data && this.salesCache.data[`${this.activeMonth}_ALL`]) {
      sliceData = this.salesCache.data[`${this.activeMonth}_ALL`];
    }

    // Toggle CF empty notice when CF is selected and no data available
    const cfNotice = document.getElementById('cf-empty-notice');
    if (cfNotice) {
      cfNotice.style.display = (this.activeChannel === 'CF' && (!sliceData || !sliceData.hasData)) ? 'block' : 'none';
    }

    if (!sliceData || !sliceData.hasData) {
      this.renderEmptyState();
      return;
    }

    // 1. Update Core Telemetry Cards
    const elRev = document.getElementById('kpi-total-revenue');
    const elMom = document.getElementById('kpi-mom-shift');
    const elMargin = document.getElementById('kpi-total-margin');
    const elMarginRate = document.getElementById('kpi-margin-rate');
    const elMhmtRev = document.getElementById('kpi-mhmt-rev');
    const elMhmtSub = document.getElementById('kpi-mhmt-subtext');
    const elInvoices = document.getElementById('kpi-invoice-volume');
    const elUnits = document.getElementById('kpi-units-volume');

    const revCrores = (sliceData.totalRevenue / 10000000).toFixed(2);
    const revLakhs = (sliceData.totalRevenue / 100000).toFixed(2);
    const marginCrores = (sliceData.totalMargin / 10000000).toFixed(2);
    const marginLakhs = (sliceData.totalMargin / 100000).toFixed(2);

    if (elRev) elRev.innerText = sliceData.totalRevenue >= 10000000 ? `₹${revCrores} Cr` : `₹${revLakhs} L`;
    if (elMom) {
      const g = sliceData.momRevenueGrowth || 0;
      elMom.innerText = g >= 0 ? `+${g}% MoM Shift` : `${g}% MoM Shift`;
      elMom.style.color = g >= 0 ? 'var(--accent-emerald)' : 'var(--accent-red)';
    }

    if (elMargin) elMargin.innerText = sliceData.totalMargin >= 10000000 ? `₹${marginCrores} Cr` : `₹${marginLakhs} L`;
    if (elMarginRate) elMarginRate.innerText = `${sliceData.marginPct || 0}% Gross Margin Rate`;

    // MHMT Vehicle Make Share KPI
    const makeSales = sliceData.makeSales || {};
    const mhmtRevCr = ((makeSales.mhmtRevenue || 0) / 10000000).toFixed(2);
    const mhmtPct = makeSales.mhmtSharePct || 0;

    if (elMhmtRev) elMhmtRev.innerText = `₹${mhmtRevCr} Cr`;
    if (elMhmtSub) elMhmtSub.innerText = `${mhmtPct}% Share (Maruti, Hyundai, Mahindra, Tata)`;

    if (elInvoices) elInvoices.innerText = (sliceData.totalInvoices || 0).toLocaleString();
    if (elUnits) elUnits.innerText = `${(sliceData.totalUnits || 0).toLocaleString()} Physical Units Sold`;

    // 2. Update 5 Master Category Cards Values
    this.updateCategoryCardsValues(sliceData.categorySales || {}, sliceData.totalRevenue);

    // 3. Render Charts
    this.renderMomTrendChart();
    this.renderMakeDistributionChart(makeSales);
    this.renderCategoryHoldingChart(sliceData.categorySales || {});

    // 4. Render Region-Wise Matrix Table
    this.renderRegionMatrix(sliceData.regionSales || []);

    // 5. Render Vehicle Make Analysis (MHMT vs OTHERS)
    this.renderMakeDashboard(makeSales);

    // 6. Render PMS Sales Dashboard Segment
    this.renderPmsDashboard(sliceData.pmsSales || {});

    // 7. Render Most Common Mechanical Aggregates Segment
    this.renderMechAggregatesDashboard(sliceData.mechAggregatesSales || []);
  },

  updateCategoryCardsValues(catSales, totalRev) {
    const categories = [
      { id: 'mech', key: 'Mechanical Parts' },
      { id: 'body', key: 'Body Parts' },
      { id: 'lubes', key: 'Lubes' },
      { id: 'elec', key: 'Electrical Parts' },
      { id: 'acc', key: 'Accessories' }
    ];

    categories.forEach(cat => {
      const val = catSales[cat.key] || 0;
      const crores = (val / 10000000).toFixed(2);
      const lakhs = (val / 100000).toFixed(2);
      const pct = ((val / (totalRev || 1)) * 100).toFixed(2);

      const elVal = document.getElementById(`cat-val-${cat.id}`);
      const elPct = document.getElementById(`cat-pct-${cat.id}`);
      const elBar = document.getElementById(`cat-bar-${cat.id}`);

      if (elVal) elVal.innerText = val >= 10000000 ? `₹${crores} Cr` : `₹${lakhs} L`;
      if (elPct) elPct.innerText = `${pct}% Sales Share`;
      if (elBar) elBar.style.width = `${pct}%`;
    });
  },

  renderEmptyState() {
    const elRev = document.getElementById('kpi-total-revenue');
    const elMargin = document.getElementById('kpi-total-margin');
    const elMhmtRev = document.getElementById('kpi-mhmt-rev');
    const elInvoices = document.getElementById('kpi-invoice-volume');

    if (elRev) elRev.innerText = "₹0.00";
    if (elMargin) elMargin.innerText = "₹0.00";
    if (elMhmtRev) elMhmtRev.innerText = "₹0.00";
    if (elInvoices) elInvoices.innerText = "0";

    const regBody = document.getElementById('region-matrix-body');
    if (regBody) {
      regBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color: var(--text-muted);">No sales data available. Upload RF/CF sales file.</td></tr>`;
    }

    const makeGrid = document.getElementById('make-cards-grid');
    if (makeGrid) {
      makeGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--text-muted);">No Make sales data available.</div>`;
    }

    const pmsGrid = document.getElementById('pms-cards-grid');
    if (pmsGrid) {
      pmsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--text-muted);">No PMS sales data available.</div>`;
    }

    const mechGrid = document.getElementById('mech-aggregates-grid');
    if (mechGrid) {
      mechGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--text-muted);">No Mechanical Aggregates sales data available.</div>`;
    }
  },

  renderMomTrendChart() {
    const ctx = document.getElementById('chart-mom-trend')?.getContext('2d');
    if (!ctx) return;

    if (this.charts.mom) this.charts.mom.destroy();

    const trendData = (this.salesCache && this.salesCache.momTrend) || [];
    const labels = trendData.map(t => t.month);
    const revValues = trendData.map(t => (t.revenue / 10000000).toFixed(2));
    const marginRates = trendData.map(t => t.marginPct);

    if (typeof Chart !== 'undefined' && labels.length > 0) {
      let gradient = ctx.createLinearGradient(0, 0, 0, 350);
      gradient.addColorStop(0, 'rgba(245, 158, 11, 0.4)');
      gradient.addColorStop(1, 'rgba(245, 158, 11, 0.0)');

      this.charts.mom = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Sales Revenue (₹ Crores)',
              data: revValues,
              borderColor: '#f59e0b',
              backgroundColor: gradient,
              borderWidth: 3,
              fill: true,
              tension: 0.4,
              pointBackgroundColor: '#f59e0b',
              pointBorderColor: '#fff',
              pointBorderWidth: 2,
              pointRadius: 5,
              pointHoverRadius: 8,
              yAxisID: 'y'
            },
            {
              label: 'Margin Rate (%)',
              data: marginRates,
              borderColor: '#10b981',
              backgroundColor: 'transparent',
              borderWidth: 2,
              borderDash: [5, 5],
              tension: 0.4,
              pointBackgroundColor: '#10b981',
              pointBorderColor: '#fff',
              pointBorderWidth: 2,
              pointRadius: 5,
              pointHoverRadius: 8,
              yAxisID: 'y1'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: {
                usePointStyle: true,
                padding: 20
              }
            }
          },
          scales: {
            x: {
              grid: { color: 'rgba(100,116,139,0.14)' },
              ticks: { color: 'var(--nx-muted)' }
            },
            y: { 
              title: { display: true, text: 'Revenue (₹ Crores)', color: '#f59e0b' },
              grid: { color: 'rgba(100,116,139,0.14)' },
              ticks: { color: 'var(--nx-muted)' }
            },
            y1: { 
              position: 'right', 
              title: { display: true, text: 'Margin (%)', color: '#10b981' }, 
              grid: { drawOnChartArea: false, color: 'rgba(100,116,139,0.14)' },
              ticks: { color: 'var(--nx-muted)' }
            }
          }
        }
      });
    }
  },

  renderMakeDistributionChart(makeSales) {
    const ctx = document.getElementById('chart-make-distribution')?.getContext('2d');
    if (!ctx) return;

    if (this.charts.make) this.charts.make.destroy();

    const items = makeSales.items || [];
    const labels = items.map(i => i.make);
    const revValues = items.map(i => (i.revenue / 10000000).toFixed(2));

    if (typeof Chart !== 'undefined' && labels.length > 0) {
      this.charts.make = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Vehicle Make Revenue (₹ Crores)',
            data: revValues,
            backgroundColor: ['#60a5fa', '#34d399', '#fbbf24', '#a78bfa', '#f472b6'],
            borderRadius: 8,
            barThickness: 40
          }]
        },
        options: { 
          responsive: true, 
          maintainAspectRatio: false,
          scales: {
            x: {
              grid: { color: 'rgba(100,116,139,0.14)' },
              ticks: { color: 'var(--nx-muted)' }
            },
            y: {
              grid: { color: 'rgba(100,116,139,0.14)' },
              ticks: { color: 'var(--nx-muted)' }
            }
          }
        }
      });
    }
  },

  renderCategoryHoldingChart(catSales) {
    const ctx = document.getElementById('chart-category-holding')?.getContext('2d');
    if (!ctx) return;

    if (this.charts.category) this.charts.category.destroy();

    const labels = Object.keys(catSales);
    const revValues = Object.values(catSales).map(v => (v / 10000000).toFixed(2));

    if (typeof Chart !== 'undefined' && labels.length > 0) {
      this.charts.category = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: revValues,
            backgroundColor: ['#a78bfa', '#60a5fa', '#34d399', '#fbbf24', '#f472b6'],
            borderWidth: 0,
            hoverOffset: 8,
            spacing: 3
          }]
        },
        options: { 
          responsive: true, 
          maintainAspectRatio: false,
          cutout: '68%',
          plugins: {
            legend: {
              position: 'right'
            }
          }
        }
      });
    }
  },

  renderRegionMatrix(regionList) {
    const tbody = document.getElementById('region-matrix-body');
    if (!tbody) return;

    if (!regionList || regionList.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:1.5rem; color:var(--text-muted);">No region sales data available.</td></tr>`;
      return;
    }

    let html = '';
    regionList.forEach(r => {
      const revCr = (r.revenue / 10000000).toFixed(2);
      const revLakhs = (r.revenue / 100000).toFixed(2);
      const displayRev = r.revenue >= 10000000 ? `₹${revCr} Cr` : `₹${revLakhs} L`;

      const marCr = (r.margin / 10000000).toFixed(2);
      const marLakhs = (r.margin / 100000).toFixed(2);
      const displayMar = r.margin >= 10000000 ? `₹${marCr} Cr` : `₹${marLakhs} L`;

      html += `
        <tr>
          <td style="font-weight:900; color:var(--accent-amber);">${r.region} REGION</td>
          <td style="font-weight:700;">${(r.invoices || 0).toLocaleString()} Lines</td>
          <td style="font-weight:900; color:var(--accent-emerald);">${displayRev}</td>
          <td><span class="badge badge-amber" style="font-weight:800;">${r.revenuePct}% Territory Share</span></td>
          <td style="font-weight:700; color:var(--accent-blue);">${displayMar}</td>
          <td><span class="badge badge-success" style="font-weight:800;">${r.marginPct}% Gross Margin</span></td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
  },

  renderMakeDashboard(makeSales) {
    const grid = document.getElementById('make-cards-grid');
    const badgeMhmt = document.getElementById('mhmt-total-badge');
    const badgeOthers = document.getElementById('others-total-badge');

    if (!makeSales || !makeSales.items) return;

    const mhmtCr = ((makeSales.mhmtRevenue || 0) / 10000000).toFixed(2);
    const othersCr = ((makeSales.othersRevenue || 0) / 10000000).toFixed(2);

    if (badgeMhmt) badgeMhmt.innerText = `MHMT Sales: ₹${mhmtCr} Cr (${makeSales.mhmtSharePct}%)`;
    if (badgeOthers) badgeOthers.innerText = `OTHERS: ₹${othersCr} Cr (${makeSales.othersSharePct}%)`;

    const iconMap = {
      'MARUTI': '🚗',
      'HYUNDAI': '🚙',
      'MAHINDRA': '🚜',
      'TATA': '🚘',
      'OTHERS': '🚐'
    };

    const colorMap = {
      'MARUTI': 'var(--accent-blue)',
      'HYUNDAI': 'var(--accent-emerald)',
      'MAHINDRA': 'var(--accent-amber)',
      'TATA': 'var(--accent-purple)',
      'OTHERS': '#ec4899'
    };

    let html = '';
    makeSales.items.forEach(item => {
      const revCr = (item.revenue / 10000000).toFixed(2);
      const revLakhs = (item.revenue / 100000).toFixed(2);
      const displayRev = item.revenue >= 10000000 ? `₹${revCr} Cr` : `₹${revLakhs} L`;

      const icon = iconMap[item.make] || '🚘';
      const color = colorMap[item.make] || 'var(--accent-blue)';
      const isMhmtTag = item.isMhmt ? `<span class="badge badge-blue" style="font-size:0.65rem;">MHMT Group</span>` : `<span class="badge badge-purple" style="font-size:0.65rem;">Others Group</span>`;

      html += `
        <div class="card" style="border: 1px solid ${color}40; padding: 1rem; border-radius: var(--radius-md);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
            <span style="font-size: 0.82rem; font-weight: 900; color: ${color}; text-transform: uppercase;">${icon} ${item.make}</span>
            ${isMhmtTag}
          </div>
          <div style="font-size: 1.35rem; font-weight: 900; color: ${color}; margin: 0.2rem 0;">${displayRev}</div>
          <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); font-weight: 700;">
            <span>Share: ${item.sharePct}%</span>
            <span>Units: ${item.units.toLocaleString()}</span>
          </div>
          <div style="background: rgba(255,255,255,0.08); height: 5px; border-radius: 3px; margin-top: 0.5rem; overflow: hidden;">
            <div style="background: ${color}; height: 100%; width: ${Math.min(item.sharePct * 3, 100)}%;"></div>
          </div>
        </div>
      `;
    });

    if (grid) grid.innerHTML = html;
  },

  renderPmsDashboard(pmsData) {
    const grid = document.getElementById('pms-cards-grid');
    const badgeTotal = document.getElementById('pms-total-badge');
    const badgeShare = document.getElementById('pms-share-badge');

    if (!pmsData || !pmsData.items) return;

    const totPmsCr = (pmsData.totalPmsRevenue / 10000000).toFixed(2);
    if (badgeTotal) badgeTotal.innerText = `PMS Sales: ₹${totPmsCr} Cr`;
    if (badgeShare) badgeShare.innerText = `${pmsData.pmsSharePct}% of Total Revenue`;

    const iconMap = {
      'Engine Oil': '🛢️',
      'Brake Pads & Discs': '🛑',
      'Clutch Disc & Cover': '⚙️',
      'Filters': '🌀',
      'Coolant & Fluids': '❄️',
      'Spark / Glow Plugs': '⚡'
    };

    const colorMap = {
      'Engine Oil': 'var(--accent-amber)',
      'Brake Pads & Discs': 'var(--accent-red)',
      'Clutch Disc & Cover': 'var(--accent-purple)',
      'Filters': 'var(--accent-blue)',
      'Coolant & Fluids': 'var(--accent-cyan)',
      'Spark / Glow Plugs': 'var(--accent-emerald)'
    };

    let html = '';
    pmsData.items.forEach(item => {
      const revCr = (item.revenue / 10000000).toFixed(2);
      const revLakhs = (item.revenue / 100000).toFixed(2);
      const displayRev = item.revenue >= 10000000 ? `₹${revCr} Cr` : `₹${revLakhs} L`;

      const icon = iconMap[item.name] || '🛠️';
      const color = colorMap[item.name] || 'var(--accent-amber)';

      html += `
        <div class="card" style="border: 1px solid ${color}40; padding: 1rem; border-radius: var(--radius-md);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
            <span style="font-size: 0.78rem; font-weight: 800; color: ${color}; text-transform: uppercase;">${icon} ${item.name}</span>
            <span class="badge badge-info" style="font-size: 0.7rem;">${item.units.toLocaleString()} units</span>
          </div>
          <div style="font-size: 1.35rem; font-weight: 900; color: ${color}; margin: 0.2rem 0;">${displayRev}</div>
          <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); font-weight: 700;">
            <span>Share: ${item.sharePct}%</span>
            <span>Margin: ${item.marginPct}%</span>
          </div>
          <div style="background: rgba(255,255,255,0.08); height: 5px; border-radius: 3px; margin-top: 0.5rem; overflow: hidden;">
            <div style="background: ${color}; height: 100%; width: ${Math.min(item.sharePct * 3.5, 100)}%;"></div>
          </div>
        </div>
      `;
    });

    if (grid) grid.innerHTML = html;
  },

  renderMechAggregatesDashboard(mechAggsList) {
    const grid = document.getElementById('mech-aggregates-grid');
    if (!grid) return;

    if (!mechAggsList || mechAggsList.length === 0) {
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 1.5rem; color: var(--text-muted);">No Mechanical Aggregates data available.</div>`;
      return;
    }

    const iconMap = {
      'BRAKE SYSTEM': '🛑',
      'CLUTCH SYSTEM': '⚙️',
      'FILTERS': '🌀',
      'SUSPENSION': '🚜',
      'STEERING': '☸️',
      'LIGHTING': '💡'
    };

    const colorMap = {
      'BRAKE SYSTEM': 'var(--accent-red)',
      'CLUTCH SYSTEM': 'var(--accent-purple)',
      'FILTERS': 'var(--accent-blue)',
      'SUSPENSION': 'var(--accent-amber)',
      'STEERING': 'var(--accent-cyan)',
      'LIGHTING': '#facc15'
    };

    let html = '';
    mechAggsList.forEach(item => {
      const revCr = (item.revenue / 10000000).toFixed(2);
      const revLakhs = (item.revenue / 100000).toFixed(2);
      const displayRev = item.revenue >= 10000000 ? `₹${revCr} Cr` : `₹${revLakhs} L`;

      const icon = iconMap[item.aggregate] || '🛠️';
      const color = colorMap[item.aggregate] || 'var(--accent-purple)';

      html += `
        <div class="card" style="border: 1.5px solid ${color}45; padding: 1.1rem; border-radius: var(--radius-md);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
            <span style="font-size: 0.8rem; font-weight: 900; color: ${color}; text-transform: uppercase;">${icon} ${item.aggregate}</span>
            <span class="badge badge-purple" style="font-size: 0.7rem;">${item.units.toLocaleString()} units</span>
          </div>
          <div style="font-size: 1.4rem; font-weight: 900; color: ${color}; margin: 0.25rem 0;">${displayRev}</div>
          <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); font-weight: 700; margin-bottom: 0.35rem;">
            <span>Share: ${item.sharePct}%</span>
            <span>Margin: ${item.marginPct}%</span>
          </div>
          <div style="font-size: 0.72rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 0.5rem;">
            Top Driver: <strong style="color: var(--text-main);">${item.topComponent}</strong>
          </div>
          <div style="background: rgba(255,255,255,0.08); height: 6px; border-radius: 3px; overflow: hidden;">
            <div style="background: ${color}; height: 100%; width: ${Math.min(item.sharePct * 4, 100)}%;"></div>
          </div>
        </div>
      `;
    });

    grid.innerHTML = html;
  }
};
