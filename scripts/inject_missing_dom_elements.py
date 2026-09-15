import os

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Inject category-valuation-cards-grid into Inventory Tab
if 'id="category-valuation-cards-grid"' not in html:
    target = '<!-- 4 CORE SCORECARDS ONLY'
    replacement = """<!-- DYNAMIC CATEGORY VALUATION SCORECARDS GRID -->
      <div id="category-valuation-cards-grid" style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 1rem; margin-bottom: 1.5rem;"></div>

      <!-- 4 CORE SCORECARDS ONLY"""
    if target in html:
        html = html.replace(target, replacement, 1)

# 2. Inject Region Map, Make Cards, Make Distribution List, and Canvas elements in Sales Tab
if 'id="region-map-grid"' not in html:
    target = '<!-- SEGMENT 1: PMS SALES DASHBOARD'
    replacement = """<!-- REGION MAP SALES DASHBOARD -->
      <div id="region-map-section" class="card" style="margin-bottom: 1.5rem; padding: 1.25rem;">
        <div style="font-size: 1.1rem; font-weight: 900; color: #ffffff; font-family: 'Outfit', sans-serif; margin-bottom: 1rem;">
          🗺️ Regional Territory Sales Breakdown (North, South, East, West)
        </div>
        <div id="region-map-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.25rem;"></div>
      </div>

      <!-- VEHICLE MAKE (MHMT) ANALYSIS DASHBOARD -->
      <div id="make-analysis-section" class="card" style="margin-bottom: 1.5rem; padding: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
          <div style="font-size: 1.1rem; font-weight: 900; color: #ffffff; font-family: 'Outfit', sans-serif;">
            🚗 Vehicle Make Revenue Distribution (Maruti, Hyundai, Mahindra, Tata & Others)
          </div>
          <span class="badge badge-info">Make Intelligence</span>
        </div>
        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1.25rem;">
          <div id="make-cards-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;"></div>
          <div style="background: rgba(15,23,42,0.8); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1rem;">
            <div style="font-size: 0.88rem; font-weight: 850; color: #ffb84d; margin-bottom: 0.75rem;">Make Share Breakdown</div>
            <div id="make-distribution-list" style="display: flex; flex-direction: column; gap: 0.6rem;"></div>
          </div>
        </div>
      </div>

      <!-- SEGMENT 1: PMS SALES DASHBOARD"""
    if target in html:
        html = html.replace(target, replacement, 1)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Injected all missing DOM elements into index.html successfully!")
