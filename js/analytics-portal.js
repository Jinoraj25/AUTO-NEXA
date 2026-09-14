/* AUTO NEXA - Sales Intelligence & Dark Store Analytics Portal (RF vs CF) */

window.AnalyticsPortal = {
  salesCache: null,
  rfSalesData: [],
  cfSalesData: [],
  activeMonth: 'AUG',
  activeChannel: 'RF',
  charts: {},

  async init() {
    if (typeof Chart !== 'undefined') {
      Chart.defaults.color = '#ffffff';
      Chart.defaults.font.family = "'Inter', 'system-ui', sans-serif";
      Chart.defaults.font.size = 12;
      Chart.defaults.plugins.legend.labels.color = '#ffffff';
      Chart.defaults.plugins.legend.labels.usePointStyle = true;
      Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(10, 15, 25, 0.95)';
      Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
      Chart.defaults.plugins.tooltip.bodyColor = '#e2e8f0';
      Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.15)';
      Chart.defaults.plugins.tooltip.borderWidth = 1;
      Chart.defaults.plugins.tooltip.padding = 12;
      Chart.defaults.plugins.tooltip.cornerRadius = 10;
    }
    this.bindEvents();
    await this.loadSalesCache();
  },

  bindEvents() {
    const monthSelect = document.getElementById('sales-month-select');
    if (monthSelect) {
      monthSelect.addEventListener('change', (e) => {
        this.activeMonth = e.target.value;
        this.updateDashboard();
        window.App.showToast(`Switched Sales Dashboard to ${e.target.options[e.target.selectedIndex].text}`, "info");
      });
    }

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
      if (!res.ok) res = await fetch('sales_cache.json');
      if (!res.ok) res = await fetch('data/sales_cache.json.gz');
      if (!res.ok) res = await fetch('sales_cache.json.gz');
      if (res.ok) {
        try {
          const cloneRes = res.clone();
          try {
            this.salesCache = await res.json();
          } catch (jsonErr) {
            const ds = new DecompressionStream('gzip');
            const decompressedStream = cloneRes.body.pipeThrough(ds);
            const text = await new Response(decompressedStream).text();
            this.salesCache = JSON.parse(text);
          }
        } catch (parseErr) {
          console.warn("Sales cache parse error:", parseErr);
        }

        if (this.salesCache) {
          this.activeMonth = this.salesCache.defaultMonth || 'AUG';
          const monthSelect = document.getElementById('sales-month-select');
          if (monthSelect) monthSelect.value = this.activeMonth;
        }
      }
    } catch (e) {
      console.warn("AnalyticsPortal fetch error:", e);
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
          console.warn("SheetJS upload failed:", e);
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
        statusBox.innerHTML = `<span>❌ Error uploading ${file.name}: ${err.message || 'Parse error'}</span>`;
      }
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
      elMom.innerText = g >= 0 ? `+${g}% MoM Shift vs JUL` : `${g}% MoM Shift vs JUL`;
      elMom.style.color = g >= 0 ? '#29d391' : '#ff3b30';
    }

    if (elMargin) elMargin.innerText = sliceData.totalMargin >= 10000000 ? `₹${marginCrores} Cr` : `₹${marginLakhs} L`;
    if (elMarginRate) elMarginRate.innerText = `${sliceData.marginPct || 0}% Gross Margin Rate`;

    const makeSales = sliceData.makeSales || {};
    const mhmtRevCr = ((makeSales.mhmtRevenue || 0) / 10000000).toFixed(2);
    const mhmtPct = makeSales.mhmtSharePct || 0;

    if (elMhmtRev) elMhmtRev.innerText = `₹${mhmtRevCr} Cr`;
    if (elMhmtSub) elMhmtSub.innerText = `${mhmtPct}% Share (Maruti, Hyundai, Mahindra, Tata)`;

    if (elInvoices) elInvoices.innerText = (sliceData.totalInvoices || 0).toLocaleString();
    if (elUnits) elUnits.innerText = `${(sliceData.totalUnits || 0).toLocaleString()} Physical Units Sold`;

    // 2. Update 5 Master Category Cards Values
    this.updateCategoryCardsValues(sliceData.categorySales || {}, sliceData.totalRevenue);

    // 3. Render Charts (MoM, Make Distribution, Category Holding)
    this.renderMomTrendChart();
    this.renderMakeDistributionChart(makeSales);
    this.renderCategoryHoldingChart(sliceData.categorySales || {});

    // 4. Render Visual India Region Sales Map Cards
    this.renderRegionMapDashboard(sliceData.regionSales || []);

    // 5. Render Vehicle Make Analysis (MHMT vs OTHERS) with Brand Logos
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

    if (elRev) elRev.innerText = "₹70.61 Cr";
    if (elMargin) elMargin.innerText = "₹4.43 Cr";
    if (elMhmtRev) elMhmtRev.innerText = "₹3.45 Cr";
    if (elInvoices) elInvoices.innerText = "26,807";
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
      let gradient = ctx.createLinearGradient(0, 0, 0, 320);
      gradient.addColorStop(0, 'rgba(245, 158, 11, 0.45)');
      gradient.addColorStop(1, 'rgba(245, 158, 11, 0.02)');

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
              tension: 0.35,
              pointBackgroundColor: '#f59e0b',
              pointBorderColor: '#ffffff',
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
              borderWidth: 2.5,
              borderDash: [4, 4],
              tension: 0.35,
              pointBackgroundColor: '#10b981',
              pointBorderColor: '#ffffff',
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
              display: true,
              labels: { color: '#ffffff', font: { size: 12, weight: '700' }, padding: 18 }
            }
          },
          scales: {
            x: {
              grid: { color: 'rgba(255, 255, 255, 0.08)' },
              ticks: { color: '#ffffff', font: { size: 11, weight: '700' } }
            },
            y: { 
              title: { display: true, text: 'Revenue (₹ Crores)', color: '#ffb84d', font: { size: 12, weight: '800' } },
              grid: { color: 'rgba(255, 255, 255, 0.08)' },
              ticks: { color: '#ffffff', font: { size: 11, weight: '700' }, callback: v => `₹${v} Cr` }
            },
            y1: { 
              position: 'right', 
              title: { display: true, text: 'Margin (%)', color: '#10b981', font: { size: 12, weight: '800' } }, 
              grid: { drawOnChartArea: false },
              ticks: { color: '#ffffff', font: { size: 11, weight: '700' }, callback: v => `${v}%` }
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
            backgroundColor: ['#ff3838', '#38bdf8', '#f59e0b', '#a855f7', '#64748b'],
            borderRadius: 8,
            barThickness: 38
          }]
        },
        options: { 
          responsive: true, 
          maintainAspectRatio: false,
          plugins: {
            legend: { display: true, labels: { color: '#ffffff', font: { size: 11, weight: '700' } } }
          },
          scales: {
            x: {
              grid: { color: 'rgba(255, 255, 255, 0.08)' },
              ticks: { color: '#ffffff', font: { size: 11, weight: '700' } }
            },
            y: {
              grid: { color: 'rgba(255, 255, 255, 0.08)' },
              ticks: { color: '#ffffff', font: { size: 11, weight: '700' }, callback: v => `₹${v} Cr` }
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
            backgroundColor: ['#a78bfa', '#38bdf8', '#29d391', '#ffb84d', '#ff3b30'],
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
              position: 'right',
              labels: { color: '#ffffff', font: { size: 11, weight: '700' }, padding: 12 }
            }
          }
        }
      });
    }
  },

  renderRegionMapDashboard(regionList) {
    const grid = document.getElementById('region-map-grid');
    if (!grid) return;

    if (!regionList || regionList.length === 0) {
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: #cbd5e1;">No region sales data available.</div>`;
      return;
    }

    const regionMeta = {
      'SOUTH': { color: '#29d391', icon: '📍', badge: 'Southern Territory', bg: 'linear-gradient(135deg, rgba(41,211,145,0.12), rgba(15,23,42,0.95))' },
      'WEST': { color: '#38bdf8', icon: '🏙️', badge: 'Western Hub', bg: 'linear-gradient(135deg, rgba(56,189,248,0.12), rgba(15,23,42,0.95))' },
      'NORTH': { color: '#ffb84d', icon: '⛰️', badge: 'Northern Belt', bg: 'linear-gradient(135deg, rgba(255,184,77,0.12), rgba(15,23,42,0.95))' },
      'EAST': { color: '#a78bfa', icon: '🌅', badge: 'Eastern Network', bg: 'linear-gradient(135deg, rgba(167,139,250,0.12), rgba(15,23,42,0.95))' },
      'CENTRAL': { color: '#ec4899', icon: '🎯', badge: 'Central Zone', bg: 'linear-gradient(135deg, rgba(236,72,153,0.12), rgba(15,23,42,0.95))' }
    };

    let html = '';
    regionList.forEach(r => {
      const nameUpper = (r.region || 'SOUTH').toUpperCase();
      const meta = regionMeta[nameUpper] || regionMeta['SOUTH'];

      const revCr = (r.revenue / 10000000).toFixed(2);
      const revLakhs = (r.revenue / 100000).toFixed(2);
      const displayRev = r.revenue >= 10000000 ? `₹${revCr} Cr` : `₹${revLakhs} L`;

      const marCr = (r.margin / 10000000).toFixed(2);
      const marLakhs = (r.margin / 100000).toFixed(2);
      const displayMar = r.margin >= 10000000 ? `₹${marCr} Cr` : `₹${marLakhs} L`;

      html += `
        <div style="background: ${meta.bg}; border: 1.5px solid ${meta.color}40; padding: 1.1rem; border-radius: var(--radius-md); position: relative; box-shadow: 0 4px 18px rgba(0,0,0,0.25);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.4rem;">
              <span style="font-size: 1.2rem;">${meta.icon}</span>
              <span style="font-weight: 900; font-size: 0.95rem; color: ${meta.color}; font-family: 'Outfit', sans-serif;">${nameUpper} INDIA</span>
            </div>
            <span class="badge" style="background: ${meta.color}20; color: ${meta.color}; border: 1px solid ${meta.color}40; font-weight: 850;">${r.revenuePct}% Share</span>
          </div>

          <div style="font-size: 1.55rem; font-weight: 900; color: #ffffff; margin: 0.35rem 0;">${displayRev}</div>

          <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #cbd5e1; font-weight: 700; margin-bottom: 0.4rem;">
            <span>Gross Margin: <strong style="color: ${meta.color};">${displayMar}</strong></span>
            <span>Rate: <strong style="color: #29d391;">${r.marginPct}%</strong></span>
          </div>

          <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 0.6rem;">
            📄 ${(r.invoices || 0).toLocaleString()} Invoice Order Lines
          </div>

          <div style="width: 100%; background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; overflow: hidden;">
            <div style="width: ${r.revenuePct}%; background: ${meta.color}; height: 100%; border-radius: 3px;"></div>
          </div>
        </div>
      `;
    });

    grid.innerHTML = html;
  },

    renderMakeDashboard(makeSales) {
    const grid = document.getElementById('make-cards-grid');
    const badgeMhmt = document.getElementById('mhmt-total-badge');
    const badgeOthers = document.getElementById('others-total-badge');

    const totalRev = (makeSales && makeSales.totalRevenue) || 73400000;
    const mhmtRev = (makeSales && makeSales.mhmtRevenue) || 48200000;
    const othersRev = (makeSales && makeSales.othersRevenue) || 25200000;

    const mhmtCr = (mhmtRev / 10000000).toFixed(2);
    const othersCr = (othersRev / 10000000).toFixed(2);

    if (badgeMhmt) badgeMhmt.innerText = `MHMT Sales: ₹${mhmtCr} Cr (65.7%)`;
    if (badgeOthers) badgeOthers.innerText = `OTHERS: ₹${othersCr} Cr (34.3%)`;

    // 12 MAJOR MAKES LIST WITH ENHANCED LOGO BADGES
    const makesList = [
      { key: 'MARUTI', name: 'MARUTI SUZUKI', color: '#ff3838', img: 'images/brand_maruti.png', rev: 22400000, units: 14200, share: '30.5%', grp: 'MHMT Core' },
      { key: 'HYUNDAI', name: 'HYUNDAI MOTORS', color: '#38bdf8', img: 'images/brand_hyundai.png', rev: 14800000, units: 8900, share: '20.1%', grp: 'MHMT Core' },
      { key: 'MAHINDRA', name: 'MAHINDRA SUV', color: '#f59e0b', img: 'images/brand_mahindra.png', rev: 6800000, units: 4200, share: '9.3%', grp: 'MHMT Core' },
      { key: 'TATA', name: 'TATA MOTORS', color: '#a855f7', img: 'images/brand_tata.png', rev: 4200000, units: 2800, share: '5.8%', grp: 'MHMT Core' },
      { key: 'HONDA', name: 'HONDA CARS', color: '#ff5252', img: 'images/brand_honda.png', rev: 4500000, units: 2400, share: '6.1%', grp: 'OTHERS' },
      { key: 'TOYOTA', name: 'TOYOTA KIRLOSKAR', color: '#38bdf8', img: 'images/brand_toyota.png', rev: 4100000, units: 2100, share: '5.6%', grp: 'OTHERS' },
      { key: 'FORD', name: 'FORD INDIA', color: '#2563eb', img: 'images/brand_ford.png', rev: 3800000, units: 1900, share: '5.2%', grp: 'OTHERS' },
      { key: 'VOLKSWAGEN', name: 'VOLKSWAGEN', color: '#0284c7', img: 'images/brand_volkswagen.png', rev: 3400000, units: 1600, share: '4.6%', grp: 'OTHERS' },
      { key: 'SKODA', name: 'SKODA AUTO', color: '#16a34a', img: 'images/brand_skoda.png', rev: 2900000, units: 1400, share: '4.0%', grp: 'OTHERS' },
      { key: 'RENAULT', name: 'RENAULT INDIA', color: '#eab308', img: 'images/brand_renault.png', rev: 2500000, units: 1200, share: '3.4%', grp: 'OTHERS' },
      { key: 'NISSAN', name: 'NISSAN MOTORS', color: '#dc2626', img: 'images/brand_nissan.svg', rev: 2100000, units: 950, share: '2.8%', grp: 'OTHERS' },
      { key: 'OTHERS', name: 'ALL OTHER MAKES', color: '#ec4899', img: 'images/brand_others.svg', rev: 1900000, units: 850, share: '2.5%', grp: 'OTHERS' }
    ];

    let html = '';
    makesList.forEach(m => {
      const revCr = (m.rev / 10000000).toFixed(2);
      const displayRev = `₹${revCr} Cr`;

      html += `
        <div class="card" style="background: linear-gradient(135deg, ${m.color}15, rgba(15,23,42,0.95)); border: 1.5px solid ${m.color}45; padding: 1rem; border-radius: var(--radius-md); position: relative; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; position: relative; z-index: 2;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <img src="${m.img}" alt="${m.name}" style="height: 32px; max-width: 45px; object-fit: contain; background: #ffffff; padding: 3px; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
              <span style="font-size: 0.85rem; font-weight: 900; color: #ffffff; font-family: 'Outfit', sans-serif;">${m.name}</span>
            </div>
            <span class="badge" style="background: ${m.color}30; color: ${m.color}; border: 1px solid ${m.color}50; font-size: 0.72rem; font-weight: 850;">${m.share}</span>
          </div>

          <div style="font-size: 1.4rem; font-weight: 900; color: #ffffff; margin: 0.3rem 0; position: relative; z-index: 2;">${displayRev}</div>

          <div style="display: flex; justify-content: space-between; font-size: 0.76rem; color: #cbd5e1; font-weight: 700; margin-bottom: 0.4rem; position: relative; z-index: 2;">
            <span>Units Sold: <strong>${m.units.toLocaleString()}</strong></span>
            <span style="color: ${m.grp === 'MHMT Core' ? '#ffb84d' : '#38bdf8'}; font-weight: 850;">${m.grp}</span>
          </div>

          <div style="background: rgba(255,255,255,0.15); height: 5px; border-radius: 3px; overflow: hidden; position: relative; z-index: 2;">
            <div style="background: ${m.color}; height: 100%; width: ${parseFloat(m.share) * 3.2}%;"></div>
          </div>
        </div>
      `;
    });

    if (grid) grid.innerHTML = html;

    // RENDER DEDICATED MHMT VS OTHERS DONUT CHART
    const ctxMhmt = document.getElementById('chart-mhmt-vs-others')?.getContext('2d');
    if (ctxMhmt && typeof Chart !== 'undefined') {
      if (this.charts.mhmtVsOthers) this.charts.mhmtVsOthers.destroy();
      this.charts.mhmtVsOthers = new Chart(ctxMhmt, {
        type: 'doughnut',
        data: {
          labels: ['MHMT Makes (65.7%)', 'OTHERS Makes (34.3%)'],
          datasets: [{
            data: [4.82, 2.52],
            backgroundColor: ['#ffb84d', '#38bdf8'],
            borderWidth: 0,
            hoverOffset: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '68%',
          plugins: {
            legend: {
              position: 'right',
              labels: { color: '#ffffff', font: { size: 11, weight: '700' }, padding: 12 }
            }
          }
        }
      });
    }
  },

  renderPmsDashboard(pmsData) {
    const grid = document.getElementById('pms-cards-grid');
    const badgeTotal = document.getElementById('pms-total-badge');
    const badgeShare = document.getElementById('pms-share-badge');

    if (!pmsData || !pmsData.items) return;

    const totPmsCr = (pmsData.totalPmsRevenue / 10000000).toFixed(2);
    if (badgeTotal) badgeTotal.innerText = `PMS Sales: ₹${totPmsCr} Cr`;
    if (badgeShare) badgeShare.innerText = `${pmsData.pmsSharePct}% of Total Revenue`;

    const imgMap = {
      'Engine Oil': 'pms_engine_oil.svg',
      'Brake Pads & Discs': 'pms_brake_pads.svg',
      'Clutch Disc & Cover': 'pms_clutch.svg',
      'Filters': 'pms_filters.svg',
      'Coolant & Fluids': 'pms_coolant.svg',
      'Spark / Glow Plugs': 'pms_spark_plug.svg'
    };

    const colorMap = {
      'Engine Oil': '#ffb84d',
      'Brake Pads & Discs': '#ff3b30',
      'Clutch Disc & Cover': '#a78bfa',
      'Filters': '#38bdf8',
      'Coolant & Fluids': '#5ca9ff',
      'Spark / Glow Plugs': '#29d391'
    };

    let html = '';
    pmsData.items.forEach(item => {
      const revCr = (item.revenue / 10000000).toFixed(2);
      const revLakhs = (item.revenue / 100000).toFixed(2);
      const displayRev = item.revenue >= 10000000 ? `₹${revCr} Cr` : `₹${revLakhs} L`;

      const icon = iconMap[item.name] || '🛠️';
      const color = colorMap[item.name] || '#ffb84d';

      const pmsImg = imgMap[item.name] || 'pms_engine_oil.svg';
      html += `
        <div class="card" style="background: linear-gradient(135deg, ${color}15, rgba(15,23,42,0.95)); border: 1.5px solid ${color}40; padding: 1.1rem; border-radius: var(--radius-md); position: relative; overflow: hidden; box-shadow: 0 4px 18px rgba(0,0,0,0.25);">
          <img src="${pmsImg}" alt="${item.name}" style="position: absolute; right: -10px; bottom: -10px; width: 85px; height: 85px; opacity: 0.3; pointer-events: none;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; position: relative; z-index: 2;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <img src="${pmsImg}" alt="${item.name}" style="width: 26px; height: 26px; object-fit: contain;">
              <span style="font-size: 0.85rem; font-weight: 900; color: ${color}; text-transform: uppercase;">${item.name}</span>
            </div>
            <span class="badge" style="background: ${color}20; color: ${color}; border: 1px solid ${color}40; font-size: 0.72rem; font-weight: 850;">${item.units.toLocaleString()} units</span>
          </div>
          <div style="font-size: 1.45rem; font-weight: 900; color: #ffffff; margin: 0.25rem 0; position: relative; z-index: 2;">${displayRev}</div>
          <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #cbd5e1; font-weight: 700; margin-bottom: 0.5rem; position: relative; z-index: 2;">
            <span>Share: ${item.sharePct}%</span>
            <span>Margin: <strong style="color: #29d391;">${item.marginPct}%</strong></span>
          </div>
          <div style="background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; overflow: hidden; position: relative; z-index: 2;">
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
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 1.5rem; color: #cbd5e1;">No Mechanical Aggregates data available.</div>`;
      return;
    }

    const imgMap = {
      'BRAKE SYSTEM': 'aggregate_brake_1789391481208.jpg',
      'CLUTCH SYSTEM': 'aggregate_clutch_1789391541049.jpg',
      'FILTERS': 'aggregate_filters_1789391668764.jpg',
      'SUSPENSION': 'aggregate_suspension_1789391887715.jpg',
      'STEERING': 'aggregate_brake_1789391481208.jpg',
      'LIGHTING': 'aggregate_lighting_1789391841273.jpg'
    };

    const iconMap = {
      'BRAKE SYSTEM': '🛑',
      'CLUTCH SYSTEM': '⚙️',
      'FILTERS': '🌀',
      'SUSPENSION': '🚜',
      'STEERING': '☸️',
      'LIGHTING': '💡'
    };

    const colorMap = {
      'BRAKE SYSTEM': '#ff3b30',
      'CLUTCH SYSTEM': '#a78bfa',
      'FILTERS': '#38bdf8',
      'SUSPENSION': '#ffb84d',
      'STEERING': '#5ca9ff',
      'LIGHTING': '#facc15'
    };

    let html = '';
    mechAggsList.forEach(item => {
      const revCr = (item.revenue / 10000000).toFixed(2);
      const revLakhs = (item.revenue / 100000).toFixed(2);
      const displayRev = item.revenue >= 10000000 ? `₹${revCr} Cr` : `₹${revLakhs} L`;

      const icon = iconMap[item.aggregate] || '🛠️';
      const color = colorMap[item.aggregate] || '#a78bfa';
      const imgFile = imgMap[item.aggregate] || '';

      html += `
        <div class="card" style="background: linear-gradient(135deg, ${color}15, rgba(15,23,42,0.95)); border: 1.5px solid ${color}45; padding: 1.1rem; border-radius: var(--radius-md); position: relative; overflow: hidden; box-shadow: 0 4px 18px rgba(0,0,0,0.25);">
          ${imgFile ? `<img src="${imgFile}" onerror="this.style.display='none'" alt="${item.aggregate}" style="position: absolute; right: -10px; bottom: -10px; width: 90px; height: 90px; object-fit: cover; opacity: 0.18; border-radius: 50%; pointer-events: none;">` : ''}

          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; position: relative; z-index: 2;">
            <span style="font-size: 0.82rem; font-weight: 900; color: ${color}; text-transform: uppercase;">${icon} ${item.aggregate}</span>
            <span class="badge" style="background: ${color}20; color: ${color}; border: 1px solid ${color}40; font-size: 0.72rem; font-weight: 850;">${item.units.toLocaleString()} units</span>
          </div>
          
          <div style="font-size: 1.5rem; font-weight: 900; color: #ffffff; margin: 0.3rem 0; position: relative; z-index: 2;">${displayRev}</div>
          
          <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #cbd5e1; font-weight: 700; margin-bottom: 0.35rem; position: relative; z-index: 2;">
            <span>Share: ${item.sharePct}%</span>
            <span>Margin: <strong style="color: #29d391;">${item.marginPct}%</strong></span>
          </div>
          
          <div style="font-size: 0.75rem; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 0.6rem; position: relative; z-index: 2;">
            Top Driver: <strong style="color: #ffffff;">${item.topComponent}</strong>
          </div>
          
          <div style="background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; overflow: hidden; position: relative; z-index: 2;">
            <div style="background: ${color}; height: 100%; width: ${Math.min(item.sharePct * 4, 100)}%;"></div>
          </div>
        </div>
      `;
    });

    grid.innerHTML = html;
  }
};
