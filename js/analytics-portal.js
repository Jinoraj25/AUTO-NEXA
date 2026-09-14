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

    const default4Regions = [
      { region: 'NORTH', name: 'NORTH REGION', revenue: 213700000, margin: 23432600, revenuePct: 30.2, marginPct: 11.0, invoices: 7327, color: '#29d391', badge: 'Northern Territory' },
      { region: 'EAST', name: 'EAST REGION', revenue: 95200000, margin: 9996000, revenuePct: 13.5, marginPct: 10.5, invoices: 3420, color: '#a78bfa', badge: 'Eastern Network' },
      { region: 'WEST', name: 'WEST REGION', revenue: 188200000, margin: 23336800, revenuePct: 26.7, marginPct: 12.4, invoices: 7140, color: '#38bdf8', badge: 'Western Hub' },
      { region: 'SOUTH', name: 'SOUTH REGION', revenue: 209000000, margin: 30932000, revenuePct: 29.6, marginPct: 14.8, invoices: 8920, color: '#ff3b30', badge: 'Southern HQ' }
    ];

    const list = (regionList && regionList.length === 4) ? regionList : default4Regions;

    let html = '';
    list.forEach(r => {
      const color = r.color || '#38bdf8';
      const revCr = (r.revenue / 10000000).toFixed(2);
      const marCr = (r.margin / 10000000).toFixed(2);

      html += `
        <div class="card" style="background: linear-gradient(135deg, ${color}15, rgba(15,23,42,0.95)); border: 1.5px solid ${color}45; padding: 1.25rem; border-radius: 14px; position: relative; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-weight: 900; font-size: 0.95rem; color: ${color}; font-family: 'Outfit', sans-serif;">📍 ${r.name || r.region}</span>
            <span class="badge" style="background: ${color}25; color: ${color}; border: 1px solid ${color}40; font-weight: 850; font-size: 0.75rem;">${r.revenuePct}% Share</span>
          </div>

          <div style="font-size: 1.7rem; font-weight: 900; color: #ffffff; margin: 0.35rem 0;">₹${revCr} Cr</div>

          <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #cbd5e1; font-weight: 700; margin-bottom: 0.5rem;">
            <span>Gross Margin: <strong style="color: ${color};">₹${marCr} Cr</strong></span>
            <span>Rate: <strong style="color: #29d391;">${r.marginPct}%</strong></span>
          </div>

          <div style="font-size: 0.78rem; color: #94a3b8; margin-bottom: 0.65rem;">
            📄 ${(r.invoices || 0).toLocaleString()} Invoice Order Lines
          </div>

          <div style="width: 100%; background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; overflow: hidden;">
            <div style="width: ${r.revenuePct * 3.2}%; background: ${color}; height: 100%; border-radius: 3px;"></div>
          </div>
        </div>
      `;
    });

    grid.innerHTML = html;
  },

      renderMakeDashboard(makeSales) {
    const grid = document.getElementById('make-cards-grid');
    const distList = document.getElementById('make-distribution-list');

    const makesList = [
      { num: '01', key: 'MARUTI', name: 'MARUTI SUZUKI', color: '#ff3838', img: 'images/brand_maruti.png', rev: 2.24, units: 14200, share: '30.5%', growth: '+6.8%', grp: 'MHMT Core' },
      { num: '02', key: 'HYUNDAI', name: 'HYUNDAI MOTORS', color: '#38bdf8', img: 'images/brand_hyundai.png', rev: 1.48, units: 8900, share: '20.1%', growth: '+4.3%', grp: 'MHMT Core' },
      { num: '03', key: 'MAHINDRA', name: 'MAHINDRA SUV', color: '#f59e0b', img: 'images/brand_mahindra.png', rev: 0.68, units: 4200, share: '9.3%', growth: '-1.2%', grp: 'MHMT Core' },
      { num: '04', key: 'TATA', name: 'TATA MOTORS', color: '#a855f7', img: 'images/brand_tata.png', rev: 0.42, units: 2800, share: '5.8%', growth: '+3.6%', grp: 'Others' },
      { num: '05', key: 'HONDA', name: 'HONDA CARS', color: '#ff5252', img: 'images/brand_honda.png', rev: 0.45, units: 2400, share: '6.1%', growth: '+2.1%', grp: 'Others' },
      { num: '06', key: 'TOYOTA', name: 'TOYOTA KIRLOSKAR', color: '#38bdf8', img: 'images/brand_toyota.png', rev: 0.41, units: 2100, share: '5.6%', growth: '+1.8%', grp: 'Others' },
      { num: '07', key: 'FORD', name: 'FORD INDIA', color: '#2563eb', img: 'images/brand_ford.png', rev: 0.38, units: 1900, share: '5.2%', growth: '-0.7%', grp: 'Others' },
      { num: '08', key: 'VOLKSWAGEN', name: 'VOLKSWAGEN', color: '#0284c7', img: 'images/brand_volkswagen.png', rev: 0.34, units: 1600, share: '4.6%', growth: '+3.4%', grp: 'Others' },
      { num: '09', key: 'SKODA', name: 'SKODA AUTO', color: '#16a34a', img: 'images/brand_skoda.png', rev: 0.29, units: 1400, share: '4.0%', growth: '+2.9%', grp: 'Others' },
      { num: '10', key: 'RENAULT', name: 'RENAULT INDIA', color: '#eab308', img: 'images/brand_renault.png', rev: 0.25, units: 1200, share: '3.4%', growth: '-1.4%', grp: 'Others' },
      { num: '11', key: 'NISSAN', name: 'NISSAN MOTORS', color: '#dc2626', img: 'images/brand_nissan.svg', rev: 0.21, units: 950, share: '2.8%', growth: '-2.6%', grp: 'Others' },
      { num: '12', key: 'OTHERS', name: 'ALL OTHER MAKES', color: '#ec4899', img: 'images/brand_others.svg', rev: 0.19, units: 850, share: '2.5%', growth: '+1.1%', grp: 'Others' }
    ];

    // 1. Render Left Grid Cards
    let htmlGrid = '';
    makesList.forEach(m => {
      const isPos = !m.growth.startswith('-');
      const growColor = isPos ? '#29d391' : '#ff3b30';

      htmlGrid += `
        <div class="card" style="background: linear-gradient(135deg, ${m.color}15, rgba(15,23,42,0.95)); border: 1.5px solid ${m.color}45; padding: 1rem; border-radius: 14px; position: relative; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
          <div style="position: absolute; top: 8px; left: 10px; font-size: 0.72rem; font-weight: 900; opacity: 0.4; color: #ffffff;">${m.num}</div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; padding-left: 1.1rem; position: relative; z-index: 2;">
            <div style="display: flex; align-items: center; gap: 0.4rem;">
              <img src="${m.img}" alt="${m.name}" style="height: 26px; max-width: 38px; object-fit: contain; background: #ffffff; padding: 2px; border-radius: 5px;">
              <span style="font-size: 0.8rem; font-weight: 900; color: #ffffff; font-family: 'Outfit', sans-serif;">${m.name}</span>
            </div>
            <span class="badge" style="background: ${m.color}30; color: ${m.color}; border: 1px solid ${m.color}50; font-size: 0.7rem; font-weight: 850;">${m.share}</span>
          </div>

          <div style="display: flex; justify-content: space-between; align-items: baseline; margin: 0.2rem 0; position: relative; z-index: 2;">
            <div style="font-size: 1.45rem; font-weight: 900; color: #ffffff;">₹${m.rev.toFixed(2)} Cr</div>
            <div style="font-size: 0.75rem; font-weight: 850; color: ${growColor};">${isPos ? '▲' : '▼'} ${m.growth}</div>
          </div>

          <div style="display: flex; justify-content: space-between; font-size: 0.74rem; color: #cbd5e1; font-weight: 700; margin-bottom: 0.4rem; position: relative; z-index: 2;">
            <span>Units Sold: <strong>${m.units.toLocaleString()}</strong></span>
            <span style="color: ${m.grp === 'MHMT Core' ? '#ffb84d' : '#cbd5e1'}; font-weight: 800;">${m.grp}</span>
          </div>

          <div style="background: rgba(255,255,255,0.15); height: 4px; border-radius: 2px; overflow: hidden; position: relative; z-index: 2;">
            <div style="background: ${m.color}; height: 100%; width: ${parseFloat(m.share) * 3}%;"></div>
          </div>
        </div>
      `;
    });

    if (grid) grid.innerHTML = htmlGrid;

    # 2. Render Right Progress Bar Rows List
    let htmlDist = '';
    makesList.forEach(m => {
      htmlDist += `
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; font-size: 0.76rem;">
          <div style="display: flex; align-items: center; gap: 0.4rem; width: 110px; min-width: 110px;">
            <img src="${m.img}" alt="${m.name}" style="height: 14px; width: 18px; object-fit: contain;">
            <span style="color: #f1f5f9; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${m.name}</span>
          </div>
          <div style="flex: 1; background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; overflow: hidden;">
            <div style="background: ${m.color}; height: 100%; width: ${parseFloat(m.share) * 3}%;"></div>
          </div>
          <div style="width: 42px; text-align: right; font-weight: 800; color: #cbd5e1;">${m.share}</div>
          <div style="width: 55px; text-align: right; font-weight: 900; color: #ffffff;">₹${m.rev.toFixed(2)} Cr</div>
        </div>
      `;
    });

    if (distList) distList.innerHTML = htmlDist;
  },

      renderPmsDashboard(pmsData) {
    const grid = document.getElementById('pms-cards-grid');
    const badgeTotal = document.getElementById('pms-total-badge');
    const badgeShare = document.getElementById('pms-share-badge');

    const defaultItems = [
      { name: 'Engine Oil', revenue: 14200000, units: 21259, sharePct: 23.32, marginPct: 18.2, img: 'images/pms_engine_oil.svg', color: '#ffb84d' },
      { name: 'Filters (Oil/Air/Fuel)', revenue: 3345000, units: 9911, sharePct: 3.53, marginPct: 15.82, img: 'images/pms_filters.svg', color: '#38bdf8' },
      { name: 'Brake Pads & Discs', revenue: 2773000, units: 4020, sharePct: 2.92, marginPct: 12.62, img: 'images/pms_brake_pads.svg', color: '#ff3b30' },
      { name: 'Clutch Disc & Cover', revenue: 1627000, units: 477, sharePct: 1.72, marginPct: 7.86, img: 'images/pms_clutch.svg', color: '#a78bfa' },
      { name: 'Coolant & Fluids', revenue: 396000, units: 2870, sharePct: 0.42, marginPct: 27.84, img: 'images/pms_coolant.svg', color: '#5ca9ff' },
      { name: 'Spark / Glow Plugs', revenue: 143000, units: 780, sharePct: 0.15, marginPct: 8.17, img: 'images/pms_spark_plug.svg', color: '#29d391' }
    ];

    const items = (pmsData && pmsData.items && pmsData.items.length > 0) ? pmsData.items : defaultItems;
    const totPmsRev = (pmsData && pmsData.totalPmsRevenue) || 30400000;
    const pmsShare = (pmsData && pmsData.pmsSharePct) || 32.05;

    if (badgeTotal) badgeTotal.innerText = `PMS Sales: ₹${(totPmsRev / 10000000).toFixed(2)} Cr`;
    if (badgeShare) badgeShare.innerText = `${pmsShare}% of Total Revenue`;

    let html = '';
    items.forEach(item => {
      const revCr = (item.revenue / 10000000).toFixed(2);
      const revLakhs = (item.revenue / 100000).toFixed(2);
      const displayRev = item.revenue >= 10000000 ? `₹${revCr} Cr` : `₹${revLakhs} L`;

      const color = item.color || '#ffb84d';
      const imgPath = item.img || 'images/pms_engine_oil.svg';

      html += `
        <div class="card" style="background: linear-gradient(135deg, ${color}18, rgba(15,23,42,0.95)); border: 1.5px solid ${color}45; padding: 1.15rem; border-radius: 14px; position: relative; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
          <img src="${imgPath}" alt="${item.name}" style="position: absolute; right: 10px; bottom: 10px; width: 65px; height: 65px; opacity: 0.85; pointer-events: none; filter: drop-shadow(0 2px 8px ${color}60);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; position: relative; z-index: 2;">
            <span style="font-size: 0.85rem; font-weight: 900; color: ${color}; text-transform: uppercase; font-family: 'Outfit', sans-serif;">🛠️ ${item.name}</span>
            <span class="badge" style="background: ${color}25; color: ${color}; border: 1px solid ${color}45; font-size: 0.72rem; font-weight: 850;">${item.units.toLocaleString()} units</span>
          </div>
          <div style="font-size: 1.55rem; font-weight: 900; color: #ffffff; margin: 0.3rem 0; position: relative; z-index: 2;">${displayRev}</div>
          <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #cbd5e1; font-weight: 700; margin-bottom: 0.55rem; position: relative; z-index: 2;">
            <span>Share: <strong>${item.sharePct}%</strong></span>
            <span>Margin: <strong style="color: #29d391;">${item.marginPct}%</strong></span>
          </div>
          <div style="background: rgba(255,255,255,0.12); height: 6px; border-radius: 3px; overflow: hidden; position: relative; z-index: 2;">
            <div style="background: ${color}; height: 100%; width: ${Math.min(item.sharePct * 3.8, 100)}%;"></div>
          </div>
        </div>
      `;
    });

    if (grid) grid.innerHTML = html;
  },

  renderMechAggregatesDashboard(mechAggsList) {
    const grid = document.getElementById('mech-aggregates-grid');
    if (!grid) return;

    const defaultAggs = [
      { aggregate: 'BRAKE SYSTEM', revenue: 18500000, units: 21400, sharePct: 18.8, marginPct: 24.5, topComponent: 'Brake Disc & Pad Kit', color: '#ff3b30', img: 'aggregate_brake_1789391481208.jpg' },
      { aggregate: 'CLUTCH SYSTEM', revenue: 14200000, units: 11200, sharePct: 14.4, marginPct: 22.8, topComponent: 'Clutch Release Bearing', color: '#a78bfa', img: 'aggregate_clutch_1789391541049.jpg' },
      { aggregate: 'FILTERS & CLEANERS', revenue: 12800000, units: 48500, sharePct: 13.0, marginPct: 21.2, topComponent: 'Air & Fuel Filter Assembly', color: '#38bdf8', img: 'aggregate_filters_1789391668764.jpg' },
      { aggregate: 'SUSPENSION & STEERING', revenue: 9800000, units: 8900, sharePct: 9.9, marginPct: 25.1, topComponent: 'Shock Absorber Front', color: '#ffb84d', img: 'aggregate_suspension_1789391887715.jpg' },
      { aggregate: 'LIGHTING & ELECTRICAL', revenue: 7400000, units: 15400, sharePct: 7.5, marginPct: 26.4, topComponent: 'Headlamp & Wiring Harness', color: '#facc15', img: 'aggregate_lighting_1789391841273.jpg' },
      { aggregate: 'ENGINE MECHANICAL', revenue: 6200000, units: 5100, sharePct: 6.3, marginPct: 28.0, topComponent: 'Timing Belt & Tensioner', color: '#5ca9ff', img: 'cat_bg_mechanical.svg' }
    ];

    const items = (mechAggsList && mechAggsList.length > 0) ? mechAggsList : defaultAggs;

    let html = '';
    items.forEach(item => {
      const revCr = (item.revenue / 10000000).toFixed(2);
      const revLakhs = (item.revenue / 100000).toFixed(2);
      const displayRev = item.revenue >= 10000000 ? `₹${revCr} Cr` : `₹${revLakhs} L`;

      const color = item.color || '#a78bfa';
      const imgFile = item.img || 'cat_bg_mechanical.svg';

      html += `
        <div class="card" style="background: linear-gradient(135deg, ${color}15, rgba(15,23,42,0.95)); border: 1.5px solid ${color}45; padding: 1.1rem; border-radius: var(--radius-md); position: relative; overflow: hidden; box-shadow: 0 4px 18px rgba(0,0,0,0.25);">
          <img src="${imgFile}" onerror="this.style.display='none'" alt="${item.aggregate}" style="position: absolute; right: -10px; bottom: -10px; width: 95px; height: 95px; object-fit: cover; opacity: 0.2; border-radius: 50%; pointer-events: none;">

          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; position: relative; z-index: 2;">
            <span style="font-size: 0.82rem; font-weight: 900; color: ${color}; text-transform: uppercase; font-family: 'Outfit', sans-serif;">⚙️ ${item.aggregate}</span>
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
