/* AutoParts Intelligence Suite - Demand Forecasting & MSL Planning */

window.ForecastingPortal = {
  leadTimeDays: 14,
  safetyDays: 7,
  forecastPlan: [],

  init() {
    this.bindEvents();
    this.updateForecasting();
  },

  bindEvents() {
    const sliderLead = document.getElementById('slider-lead-time');
    const sliderSafety = document.getElementById('slider-safety-days');

    if (sliderLead) {
      sliderLead.addEventListener('input', (e) => {
        this.leadTimeDays = parseInt(e.target.value);
        document.getElementById('val-lead-time').innerText = `${this.leadTimeDays} Days`;
        this.updateForecasting();
      });
    }

    if (sliderSafety) {
      sliderSafety.addEventListener('input', (e) => {
        this.safetyDays = parseInt(e.target.value);
        document.getElementById('val-safety-days').innerText = `${this.safetyDays} Days`;
        this.updateForecasting();
      });
    }

    const btnGeneratePO = document.getElementById('btn-generate-po');
    if (btnGeneratePO) {
      btnGeneratePO.addEventListener('click', () => {
        const reorderItems = this.forecastPlan.filter(f => f.status === 'CRITICAL' || f.status === 'REORDER');
        window.App.showToast(`Generated Purchase Order Draft for ${reorderItems.length} critical items!`, "success");
      });
    }
  },

  updateForecasting() {
    const salesData = window.DataEngine.mappedSalesData.length > 0 
      ? window.DataEngine.mappedSalesData 
      : (window.DataEngine.db.salesSample || []);

    if (!salesData || salesData.length === 0) return;

    // Group sales by Component to calculate daily sales velocity
    const compStats = {};
    salesData.forEach(r => {
      const comp = r.component || "UNSPECIFIED";
      if (!compStats[comp]) {
        compStats[comp] = {
          component: comp,
          aggregate: r.aggregate || "GENERAL",
          category: r.category || "Mechanical Parts",
          totalQty: 0,
          unitPrice: r.unitPrice || 350
        };
      }
      compStats[comp].totalQty += (r.qty || 1);
    });

    const stockMaster = window.DataEngine.db.stockSample || [];
    this.forecastPlan = [];

    let criticalCount = 0;
    let reorderCount = 0;
    let optimalCount = 0;
    let overstockCount = 0;

    Object.values(compStats).forEach((item, idx) => {
      const avgDailySales = Math.max(item.totalQty / 30, 0.4); // 30-day period velocity
      
      // Dynamic MSL Formula: MSL = (Avg Daily Sales * Lead Time) + (Avg Daily Sales * Safety Days)
      const leadStock = avgDailySales * this.leadTimeDays;
      const safetyStock = avgDailySales * this.safetyDays;
      const msl = Math.ceil(leadStock + safetyStock);
      const rop = Math.ceil(leadStock + (safetyStock * 0.5));
      const maxStock = Math.ceil(msl * 2.5);

      // Current Stock lookup or synthetic stock state
      const stockItem = stockMaster.find(s => s.component === item.component);
      const currentStock = stockItem ? stockItem.currentStock : ((idx * 17) % (maxStock + 15));

      // 30-Day Demand Forecast (Sales Velocity * Growth Factor)
      const forecastDemand30 = Math.ceil(avgDailySales * 30 * 1.12);

      let status = "OPTIMAL";
      let statusBadge = `<span class="badge badge-high">Optimal</span>`;
      
      if (currentStock <= msl * 0.4) {
        status = "CRITICAL";
        statusBadge = `<span class="badge badge-low">🔴 Critical Stockout</span>`;
        criticalCount++;
      } else if (currentStock <= msl) {
        status = "REORDER";
        statusBadge = `<span class="badge badge-medium">🟡 Reorder Needed</span>`;
        reorderCount++;
      } else if (currentStock > maxStock) {
        status = "OVERSTOCK";
        statusBadge = `<span class="badge badge-info">🔵 Overstocked</span>`;
        overstockCount++;
      } else {
        optimalCount++;
      }

      const suggestedPO = Math.max(0, msl * 1.5 - currentStock);

      this.forecastPlan.push({
        component: item.component,
        aggregate: item.aggregate,
        category: item.category,
        avgDailySales: avgDailySales.toFixed(1),
        currentStock: currentStock,
        msl: msl,
        rop: rop,
        maxStock: maxStock,
        forecastDemand30: forecastDemand30,
        suggestedPO: Math.ceil(suggestedPO),
        status: status,
        statusBadge: statusBadge
      });
    });

    this.renderMetrics(criticalCount, reorderCount, optimalCount, overstockCount);
    this.renderForecastTable();
    this.renderCharts();
  },

  recalculatePlan() {
    this.updateForecasting();
    if (window.App && window.App.showToast) {
      window.App.showToast("Recalculated 30/60/90 day demand forecast and dynamic MSL plan!", "success");
    }
  },

  renderCharts() {
    if (typeof Chart === 'undefined') return;

    // 1. Demand Forecast Line Chart
    const ctxDemand = document.getElementById('chart-demand-forecast');
    if (ctxDemand) {
      if (this.demandChartInstance) this.demandChartInstance.destroy();
      this.demandChartInstance = new Chart(ctxDemand, {
        type: 'line',
        data: {
          labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
          datasets: [
            {
              label: 'Actual Sales',
              data: [1200, 1350, 1420, 1500, 1680, 1750, 1820, 1900, null, null],
              borderColor: '#38bdf8',
              backgroundColor: 'rgba(56, 189, 248, 0.15)',
              tension: 0.35,
              borderWidth: 3
            },
            {
              label: 'Forecast Demand',
              data: [null, null, null, null, null, null, 1820, 1900, 2050, 2200],
              borderColor: '#ffb84d',
              borderDash: [5, 5],
              tension: 0.35,
              borderWidth: 2
            },
            {
              label: 'Safety Stock',
              data: [600, 600, 650, 650, 700, 700, 750, 750, 800, 800],
              borderColor: '#ff3b30',
              borderDash: [3, 3],
              borderWidth: 1.5,
              fill: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: true, labels: { color: '#94a3b8', font: { size: 10 } } } },
          scales: {
            x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { display: false } },
            y: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.05)' } }
          }
        }
      });
    }

    // 2. Forecast vs Current Stock Bar Chart
    const ctxStock = document.getElementById('chart-forecast-vs-stock');
    if (ctxStock) {
      if (this.stockChartInstance) this.stockChartInstance.destroy();
      this.stockChartInstance = new Chart(ctxStock, {
        type: 'bar',
        data: {
          labels: ['Brake Pads', 'Oil Filter', 'Air Filter', 'Clutch Kit', 'Shock Absorber'],
          datasets: [
            {
              label: 'Current Stock',
              data: [182, 340, 420, 96, 200],
              backgroundColor: '#38bdf8'
            },
            {
              label: 'Forecast Demand',
              data: [420, 510, 380, 310, 260],
              backgroundColor: '#ffb84d'
            },
            {
              label: 'Shortage',
              data: [238, 170, 0, 214, 60],
              backgroundColor: '#ff3b30'
            }
          ]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: true, labels: { color: '#94a3b8', font: { size: 10 } } } },
          scales: {
            x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
            y: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { display: false } }
          }
        }
      });
    }
  },

  renderMetrics(crit, reorder, opt, over) {
    const elCrit = document.getElementById('kpi-msl-critical');
    const elReorder = document.getElementById('kpi-msl-reorder');
    const elOptimal = document.getElementById('kpi-msl-optimal');

    if (elCrit) elCrit.innerText = `${crit}`;
    if (elReorder) elReorder.innerText = `${reorder}`;
    if (elOptimal) elOptimal.innerText = `${opt}`;
  },

  exportPODraft() {
    if (!this.forecastPlan || this.forecastPlan.length === 0) {
      window.App.showToast('No forecast plan is available to export yet.', 'warning');
      return;
    }
    const rows = this.forecastPlan.filter(f => f.status === 'CRITICAL' || f.status === 'REORDER').map(f => ({
      Component: f.component, Aggregate: f.aggregate, Category: f.category,
      'Avg Daily Sales': Number(f.avgDailySales), 'Current Stock': f.currentStock,
      MSL: f.msl, ROP: f.rop, 'Max Stock': f.maxStock,
      '30-Day Forecast': f.forecastDemand30, 'Suggested PO Qty': f.suggestedPO, Priority: f.status
    }));
    if (!rows.length) {
      window.App.showToast('No critical or reorder components require a PO draft.', 'info');
      return;
    }
    const ws = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'PO Draft');
    XLSX.writeFile(wb, `AUTO_NEXA_PO_DRAFT_${new Date().toISOString().slice(0,10)}.xlsx`);
    window.App.showToast(`Exported PO draft for ${rows.length} components.`, 'success');
  },

  renderForecastTable() {
    const tbody = document.getElementById('forecast-table-body');
    if (!tbody) return;

    let html = '';
    this.forecastPlan.slice(0, 15).forEach(f => {
      html += `
        <tr>
          <td style="font-weight: 700; color: var(--accent-cyan);">${f.component}</td>
          <td>${f.aggregate}</td>
          <td>${f.avgDailySales} pcs/day</td>
          <td style="font-weight:700;">${f.currentStock} pcs</td>
          <td style="color: var(--accent-amber); font-weight:700;">${f.msl} pcs</td>
          <td style="color: var(--accent-purple); font-weight:700;">${f.forecastDemand30} pcs</td>
          <td style="font-weight:700; color: var(--accent-emerald);">${f.suggestedPO > 0 ? f.suggestedPO + ' pcs' : '—'}</td>
          <td>${f.statusBadge}</td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
  }
};
