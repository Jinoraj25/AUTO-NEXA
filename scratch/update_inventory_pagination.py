with open('js/inventory-portal.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Add pagination properties to InventoryPortal object definition
code_updated = code.replace("  filteredItems: [],", "  filteredItems: [],\n  currentPage: 1,\n  pageSize: 50,")

# Reset currentPage in applyFiltersAndRenderTable
code_updated = code_updated.replace("    this.filteredItems = resList;\n    this.renderTable();", "    this.filteredItems = resList;\n    this.currentPage = 1;\n    this.renderTable();")

# Replace renderTable with paginated renderTable & renderInventoryPagination
old_render_table = '''  renderTable() {
    const tbody = document.getElementById('inventory-table-body');
    if (!tbody) return;

    if (!this.filteredItems || this.filteredItems.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="13" style="text-align:center; padding: 2.5rem; color: #94a3b8;">
            No stock records matching FILTER (${this.selectedTag}) and search query "${this.searchQuery}" for ${this.selectedDate}.
          </td>
        </tr>
      `;
      return;
    }

    const displayItems = this.filteredItems;

    let html = '';
    displayItems.forEach(item => {
      const sourceVal = item.source || item.Source || item.channel || 'myTVS';
      const branchCode = item.branchCode || item.branch || 'WHM';
      const branchName = item.branchName || 'MADURAI';

      html += `
        <tr>
          <td style="font-size: 0.78rem; font-weight: 850;"><span class="badge" style="background: rgba(167,139,250,0.18); color: #a78bfa; border: 1px solid rgba(167,139,250,0.35); font-size: 0.72rem; font-weight: 850;">${sourceVal}</span></td>
          <td style="font-family: monospace; font-weight: 850; color: #ffb84d; font-size: 0.85rem;">${item.partNo || '—'}</td>
          <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #ffffff;" title="${item.desc}">${item.desc}</td>
          <td><span class="badge badge-info" style="font-size: 0.72rem; font-weight: 800;">${item.brand || 'GENERIC'}</span></td>
          <td style="font-weight: 700; color: #38bdf8;">${item.category}</td>
          <td style="font-size: 0.8rem; color: #94a3b8;">${item.lineCode || '—'}</td>
          <td style="font-family: monospace; font-weight: 850; font-size: 0.8rem; color: #a78bfa;">${branchCode}</td>
          <td style="font-size: 0.8rem; color: #94a3b8;">${branchName}</td>
          <td style="font-weight: 850; text-align: right; color: #ffffff;">${item.qty} pcs</td>
          <td style="color: #94a3b8; text-align: right;">₹${(item.unitCost || 0).toFixed(2)}</td>
          <td style="color: #94a3b8; text-align: right;">₹${(item.mrp || 0).toFixed(2)}</td>
          <td style="font-weight: 850; color: #29d391; text-align: right;">₹${(item.valuation || 0).toLocaleString('en-IN', {maximumFractionDigits: 0})}</td>
          <td style="font-size: 0.8rem; color: #94a3b8; text-align: right;">${item.ageDays || 12} d</td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
  },'''

new_render_table = '''  renderTable() {
    const tbody = document.getElementById('inventory-table-body');
    if (!tbody) return;

    if (!this.filteredItems || this.filteredItems.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="13" style="text-align:center; padding: 2.5rem; color: #94a3b8;">
            No stock records matching FILTER (${this.selectedTag}) and search query "${this.searchQuery}" for ${this.selectedDate}.
          </td>
        </tr>
      `;
      this.renderInventoryPagination(0);
      return;
    }

    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    const displayItems = this.filteredItems.slice(start, end);

    let html = '';
    displayItems.forEach(item => {
      const sourceVal = item.source || item.Source || item.channel || 'myTVS';
      const branchCode = item.branchCode || item.branch || 'WHM';
      const branchName = item.branchName || 'MADURAI';

      html += `
        <tr>
          <td style="font-size: 0.78rem; font-weight: 850;"><span class="badge" style="background: rgba(167,139,250,0.18); color: #a78bfa; border: 1px solid rgba(167,139,250,0.35); font-size: 0.72rem; font-weight: 850;">${sourceVal}</span></td>
          <td style="font-family: monospace; font-weight: 850; color: #ffb84d; font-size: 0.85rem;">${item.partNo || '—'}</td>
          <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #ffffff;" title="${item.desc}">${item.desc}</td>
          <td><span class="badge badge-info" style="font-size: 0.72rem; font-weight: 800;">${item.brand || 'GENERIC'}</span></td>
          <td style="font-weight: 700; color: #38bdf8;">${item.category}</td>
          <td style="font-size: 0.8rem; color: #94a3b8;">${item.lineCode || '—'}</td>
          <td style="font-family: monospace; font-weight: 850; font-size: 0.8rem; color: #a78bfa;">${branchCode}</td>
          <td style="font-size: 0.8rem; color: #94a3b8;">${branchName}</td>
          <td style="font-weight: 850; text-align: right; color: #ffffff;">${item.qty} pcs</td>
          <td style="color: #94a3b8; text-align: right;">₹${(item.unitCost || 0).toFixed(2)}</td>
          <td style="color: #94a3b8; text-align: right;">₹${(item.mrp || 0).toFixed(2)}</td>
          <td style="font-weight: 850; color: #29d391; text-align: right;">₹${(item.valuation || 0).toLocaleString('en-IN', {maximumFractionDigits: 0})}</td>
          <td style="font-size: 0.8rem; color: #94a3b8; text-align: right;">${item.ageDays || 12} d</td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
    this.renderInventoryPagination(this.filteredItems.length);
  },

  renderInventoryPagination(totalCount) {
    const pagContainer = document.getElementById('inventory-pagination');
    if (!pagContainer) return;

    const count = (typeof totalCount === 'number') ? totalCount : (this.filteredItems ? this.filteredItems.length : 0);
    const totalPages = Math.ceil(count / this.pageSize) || 1;
    if (this.currentPage > totalPages) this.currentPage = totalPages;

    const startItem = count > 0 ? (this.currentPage - 1) * this.pageSize + 1 : 0;
    const endItem = Math.min(this.currentPage * this.pageSize, count);

    pagContainer.innerHTML = `
      <div style="font-size:0.8rem; color:var(--text-muted);">
        Showing ${startItem} to ${endItem} of ${count.toLocaleString()} stock items
      </div>
      <div style="display:flex; gap:0.5rem; align-items:center;">
        <button class="btn btn-secondary" style="padding:0.25rem 0.65rem; font-size:0.75rem;" ${this.currentPage <= 1 ? 'disabled' : ''} onclick="InventoryPortal.changePage(${this.currentPage - 1})">Prev</button>
        <span style="font-size:0.85rem; font-weight:700; padding: 0.2rem 0.5rem;">${this.currentPage} / ${totalPages}</span>
        <button class="btn btn-secondary" style="padding:0.25rem 0.65rem; font-size:0.75rem;" ${this.currentPage >= totalPages ? 'disabled' : ''} onclick="InventoryPortal.changePage(${this.currentPage + 1})">Next</button>
      </div>
    `;
  },

  changePage(page) {
    this.currentPage = page;
    this.renderTable();
  },'''

code_updated = code_updated.replace(old_render_table, new_render_table)

with open('js/inventory-portal.js', 'w', encoding='utf-8') as f:
    f.write(code_updated)

print("Updated js/inventory-portal.js with paginated full-stock search grid!")
