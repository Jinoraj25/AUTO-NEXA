import os
import re

# 1. Update MappingPortal in js/mapping-portal.js
with open("js/mapping-portal.js", "r", encoding="utf-8") as f:
    mapping_code = f.read()

# Fix init() to ensure rules are available immediately
old_mapping_init = """  init() {
    this.bindEvents();
    this.filteredMaster = [...(window.DataEngine.db.aggregateMaster || [])];
    this.renderAggregateMasterTable();
  },"""

new_mapping_init = """  init() {
    this.bindEvents();
    if (window.DataEngine) {
      if (!window.DataEngine.db.aggregateMaster || window.DataEngine.db.aggregateMaster.length === 0) {
        window.DataEngine.initDefaultRules();
      }
      this.filteredMaster = [...(window.DataEngine.db.aggregateMaster || [])];
    }
    this.renderAggregateMasterTable();
  },"""

if old_mapping_init in mapping_code:
    mapping_code = mapping_code.replace(old_mapping_init, new_mapping_init)

with open("js/mapping-portal.js", "w", encoding="utf-8") as f:
    f.write(mapping_code)

print("Updated js/mapping-portal.js")

# 2. Update InventoryPortal in js/inventory-portal.js
with open("js/inventory-portal.js", "r", encoding="utf-8") as f:
    inv_code = f.read()

# Remove duplicated renderTrendChart
if inv_code.count("renderTrendChart()") > 3:
    # Clean up duplicate method
    inv_code = re.sub(r"renderTrendChart\(\)\s*\{[^}]*Chart\.getChart\('chart-inventory-valuation-trend'\)[^}]*\}\s*,\s*renderTrendChart\(\)", "renderTrendChart()", inv_code)

with open("js/inventory-portal.js", "w", encoding="utf-8") as f:
    f.write(inv_code)

print("Updated js/inventory-portal.js")

# 3. Update switchTab in js/app.js to guarantee chart resize on tab change
with open("js/app.js", "r", encoding="utf-8") as f:
    app_code = f.read()

old_switch = """    try {
      if (this.activeTab === 'inventory' && window.InventoryPortal) {
        window.InventoryPortal.fetchInventoryData();
      } else if (this.activeTab === 'analytics' && window.AnalyticsPortal) {
        window.AnalyticsPortal.updateDashboard();
      } else if (this.activeTab === 'deviation' && window.DeviationPortal) {
        window.DeviationPortal.updateDeviationAnalysis();
      } else if (this.activeTab === 'forecasting' && window.ForecastingPortal) {
        window.ForecastingPortal.updateForecasting();
      }
    } catch (tabErr) {
      console.warn("Tab switch callback warning:", tabErr);
    }"""

new_switch = """    setTimeout(() => {
      try {
        if (this.activeTab === 'inventory' && window.InventoryPortal) {
          window.InventoryPortal.renderAll();
        } else if (this.activeTab === 'analytics' && window.AnalyticsPortal) {
          window.AnalyticsPortal.updateDashboard();
        } else if (this.activeTab === 'catalogue' && window.MappingPortal) {
          window.MappingPortal.renderAggregateMasterTable();
        } else if (this.activeTab === 'deviation' && window.DeviationPortal) {
          window.DeviationPortal.updateDeviationAnalysis();
        } else if (this.activeTab === 'forecasting' && window.ForecastingPortal) {
          window.ForecastingPortal.updateForecasting();
        }
      } catch (tabErr) {
        console.warn("Tab switch callback warning:", tabErr);
      }
    }, 60);"""

if old_switch in app_code:
    app_code = app_code.replace(old_switch, new_switch)

with open("js/app.js", "w", encoding="utf-8") as f:
    f.write(app_code)

print("Updated js/app.js")
