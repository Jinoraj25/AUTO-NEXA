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
  },

  renderMetrics(crit, reorder, opt, over) {
    const elCrit = document.getElementById('kpi-msl-critical');
    const elReorder = document.getElementById('kpi-msl-reorder');
    const elOptimal = document.getElementById('kpi-msl-optimal');

    if (elCrit) elCrit.innerText = `${crit} Components`;
    if (elReorder) elReorder.innerText = `${reorder} Components`;
    if (elOptimal) elOptimal.innerText = `${opt} Components`;
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
