import os, re

print("=== Adding Live Mapped Output Table & Pagination to mapping-portal.js & index.html (v72) ===")

# 1. Update index.html to add mapped-dataset-list container inside mapping-summary-section
index_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\index.html"
with open(index_path, "r", encoding="utf-8") as f:
    html_code = f.read()

mapped_table_html = """          <!-- Mapped Uploaded File Dataset Live Table -->
          <div style="margin-top: 1.5rem; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 1.25rem;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.75rem;">
              <div>
                <h4 style="font-size: 1.05rem; font-weight: 850; color: #38bdf8; margin: 0;">📋 Uploaded Catalogue Live Mapped Results</h4>
                <p style="font-size: 0.8rem; color: #94a3b8; margin: 0.25rem 0 0 0;">Interactive preview of mapped components and TVS Aggregate Master assignments.</p>
              </div>
              <input type="text" id="mapped-table-search" placeholder="Search mapped rows (Part, Desc, Aggregate)..." oninput="MappingPortal.renderMappedDatasetTable(this.value)" style="background: rgba(255, 255, 255, 0.06); border: 1.5px solid rgba(56, 189, 248, 0.35); border-radius: 8px; padding: 0.45rem 0.85rem; color: #fff; font-size: 0.8rem; width: 280px;">
            </div>

            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th style="color: #94a3b8; font-weight: 850;">Part Code</th>
                    <th style="color: #ffffff; font-weight: 850;">Item Description</th>
                    <th style="color: #cbd5e1; font-weight: 850;">Brand</th>
                    <th style="color: #38bdf8; font-weight: 850;">Mapped Aggregate</th>
                    <th style="color: #a78bfa; font-weight: 850;">Mapped Sub-Aggregate</th>
                    <th style="color: #29d391; font-weight: 850;">Mapped Component</th>
                    <th style="color: #fbbf24; font-weight: 850;">Match Method</th>
                  </tr>
                </thead>
                <tbody id="mapped-dataset-list">
                  <!-- Mapped file rows dynamically rendered here -->
                </tbody>
              </table>
            </div>

            <div id="mapped-dataset-pagination" style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
              <!-- Pagination controls -->
            </div>
          </div>
        </div>"""

old_summary_close = """              <div id="map-stat-confidence" class="card-value" style="font-size: 1.3rem; color: var(--accent-blue);">100% High</div>
            </div>
          </div>
        </div>"""

if "mapped-dataset-list" not in html_code:
    if old_summary_close in html_code:
        html_code = html_code.replace(old_summary_close, """              <div id="map-stat-confidence" class="card-value" style="font-size: 1.3rem; color: var(--accent-blue);">100% High</div>
            </div>
""" + mapped_table_html, 1)
        print("Inserted live mapped dataset table into index.html")
    else:
        print("WARNING: Summary close section not matched in index.html")

with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_code)


# 2. Update js/mapping-portal.js to add renderMappedDatasetTable and changeMappedPage
mp_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\mapping-portal.js"
with open(mp_path, "r", encoding="utf-8") as f:
    mp_code = f.read()

new_render_methods = """  mappedCurrentPage: 1,
  mappedPageSize: 15,
  filteredMappedList: [],

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

    // Render Live Mapped Table for Uploaded Dataset
    this.mappedCurrentPage = 1;
    this.renderMappedDatasetTable();
  },

  renderMappedDatasetTable(queryOverride) {
    const tbody = document.getElementById('mapped-dataset-list');
    if (!tbody) return;

    const data = (window.DataEngine && window.DataEngine.mappedSalesData && window.DataEngine.mappedSalesData.length > 0)
      ? window.DataEngine.mappedSalesData
      : [];

    const searchInput = document.getElementById('mapped-table-search');
    const rawQuery = (typeof queryOverride === 'string') ? queryOverride : (searchInput ? searchInput.value : "");
    const q = String(rawQuery || "").trim().toLowerCase();

    let listToRender = data;
    if (q) {
      listToRender = data.filter(item => {
        return (item.partNo && item.partNo.toLowerCase().includes(q)) ||
               (item.description && item.description.toLowerCase().includes(q)) ||
               (item.brand && item.brand.toLowerCase().includes(q)) ||
               (item.aggregate && item.aggregate.toLowerCase().includes(q)) ||
               (item.subAggregate && item.subAggregate.toLowerCase().includes(q)) ||
               (item.component && item.component.toLowerCase().includes(q));
      });
    }

    this.filteredMappedList = listToRender;

    if (!listToRender || listToRender.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: #94a3b8;">No mapped dataset rows matching search query "${q}".</td></tr>`;
      this.renderMappedPagination(0);
      return;
    }

    const start = (this.mappedCurrentPage - 1) * this.mappedPageSize;
    const end = start + this.mappedPageSize;
    const pageItems = listToRender.slice(start, end);

    let html = '';
    pageItems.forEach(item => {
      const methodStr = item.matchMethod || 'DOMAIN_KEYWORD_MATCH';
      const badgeBg = methodStr.includes('EXACT') ? '#29d39120' : (methodStr.includes('DOMAIN') ? '#38bdf820' : (methodStr.includes('TOKEN') ? '#a78bfa20' : '#ffb84d20'));
      const badgeColor = methodStr.includes('EXACT') ? '#29d391' : (methodStr.includes('DOMAIN') ? '#38bdf8' : (methodStr.includes('TOKEN') ? '#a78bfa' : '#ffb84d'));

      html += `
        <tr>
          <td style="font-weight: 700; color: #cbd5e1; font-family: monospace;">${item.partNo || '-'}</td>
          <td style="font-weight: 850; color: #ffffff; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${item.description}">${item.description || '-'}</td>
          <td style="font-weight: 700; color: #94a3b8;">${item.brand || 'GENERIC'}</td>
          <td style="font-weight: 850; color: #38bdf8;">${item.aggregate || 'GENERAL SPARES'}</td>
          <td style="font-weight: 700; color: #a78bfa;">${item.subAggregate || 'GENERAL'}</td>
          <td style="font-weight: 850; color: #29d391;">${item.component || 'GENERAL SPARES'}</td>
          <td><span class="badge" style="background: ${badgeBg}; color: ${badgeColor}; border: 1px solid ${badgeColor}40; font-size: 0.7rem; font-weight: 850;">${methodStr}</span></td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
    this.renderMappedPagination(listToRender.length);
  },

  renderMappedPagination(totalCount) {
    const pagContainer = document.getElementById('mapped-dataset-pagination');
    if (!pagContainer) return;

    const count = (typeof totalCount === 'number') ? totalCount : (this.filteredMappedList ? this.filteredMappedList.length : 0);
    const totalPages = Math.ceil(count / this.mappedPageSize) || 1;
    if (this.mappedCurrentPage > totalPages) this.mappedCurrentPage = totalPages;

    const startItem = count > 0 ? (this.mappedCurrentPage - 1) * this.mappedPageSize + 1 : 0;
    const endItem = Math.min(this.mappedCurrentPage * this.mappedPageSize, count);

    pagContainer.innerHTML = `
      <div style="font-size:0.8rem; color:var(--text-muted);">
        Showing ${startItem} to ${endItem} of ${count.toLocaleString()} mapped file rows
      </div>
      <div style="display:flex; gap:0.5rem;">
        <button class="btn btn-secondary" style="padding:0.25rem 0.65rem; font-size:0.75rem;" ${this.mappedCurrentPage <= 1 ? 'disabled' : ''} onclick="MappingPortal.changeMappedPage(${this.mappedCurrentPage - 1})">Prev</button>
        <span style="font-size:0.85rem; font-weight:700; padding: 0.2rem 0.5rem; color: #fff;">${this.mappedCurrentPage} / ${totalPages}</span>
        <button class="btn btn-secondary" style="padding:0.25rem 0.65rem; font-size:0.75rem;" ${this.mappedCurrentPage >= totalPages ? 'disabled' : ''} onclick="MappingPortal.changeMappedPage(${this.mappedCurrentPage + 1})">Next</button>
      </div>
    `;
  },

  changeMappedPage(page) {
    this.mappedCurrentPage = page;
    this.renderMappedDatasetTable();
  },"""

summary_start = mp_code.find("renderMappingSummary(mappedData) {")
if summary_start != -1:
    summary_end = mp_code.find("filterByAggregateCard(aggName) {", summary_start)
    if summary_end != -1:
        mp_code = mp_code[:summary_start] + new_render_methods + "\n\n  " + mp_code[summary_end:]
        print("Replaced renderMappingSummary and added renderMappedDatasetTable into js/mapping-portal.js")

with open(mp_path, "w", encoding="utf-8") as f:
    f.write(mp_code)

print("Done updating mapping-portal.js and index.html!")
