import re

with open('js/mapping-portal.js', 'r', encoding='utf-8') as f:
    code = f.read()

new_methods = '''  filterMasterTable(query = "") {
    if (!window.DataEngine || !window.DataEngine.db || !Array.isArray(window.DataEngine.db.aggregateMaster) || window.DataEngine.db.aggregateMaster.length === 0) {
      if (window.DataEngine && typeof window.DataEngine.initDefaultRules === 'function') {
        window.DataEngine.initDefaultRules();
      }
    }

    const fullMaster = (window.DataEngine && window.DataEngine.db && Array.isArray(window.DataEngine.db.aggregateMaster))
      ? window.DataEngine.db.aggregateMaster
      : [];

    const q = String(query || "").trim().toLowerCase();
    if (!q) {
      this.filteredMaster = [...fullMaster];
    } else {
      this.filteredMaster = fullMaster.filter(item => {
        return (item.aggregate && item.aggregate.toLowerCase().includes(q)) ||
               (item.subAggregate && item.subAggregate.toLowerCase().includes(q)) ||
               (item.component && item.component.toLowerCase().includes(q)) ||
               (item.category && item.category.toLowerCase().includes(q));
      });
    }
    this.masterCurrentPage = 1;
    this.renderAggregateMasterTable();
  },

  renderAggregateMasterTable() {
    const tbody = document.getElementById('master-rules-list');
    if (!tbody) return;

    if (!window.DataEngine || !window.DataEngine.db || !Array.isArray(window.DataEngine.db.aggregateMaster) || window.DataEngine.db.aggregateMaster.length === 0) {
      if (window.DataEngine && typeof window.DataEngine.initDefaultRules === 'function') {
        window.DataEngine.initDefaultRules();
      }
    }

    const fullMaster = (window.DataEngine && window.DataEngine.db && Array.isArray(window.DataEngine.db.aggregateMaster))
      ? window.DataEngine.db.aggregateMaster
      : [];

    const searchInput = document.getElementById('master-search-input');
    const q = (searchInput ? searchInput.value : "").trim().toLowerCase();

    if (!this.filteredMaster || (!q && this.filteredMaster.length === 0 && fullMaster.length > 0)) {
      if (q) {
        this.filteredMaster = fullMaster.filter(item => {
          return (item.aggregate && item.aggregate.toLowerCase().includes(q)) ||
                 (item.subAggregate && item.subAggregate.toLowerCase().includes(q)) ||
                 (item.component && item.component.toLowerCase().includes(q)) ||
                 (item.category && item.category.toLowerCase().includes(q));
        });
      } else {
        this.filteredMaster = [...fullMaster];
      }
    }

    const listToRender = (this.filteredMaster !== undefined && this.filteredMaster !== null) ? this.filteredMaster : fullMaster;

    if (!listToRender || listToRender.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 2.5rem; color: #94a3b8;">No aggregate master rules matching search query "${q}".</td></tr>`;
      this.renderMasterPagination(0);
      return;
    }

    const start = (this.masterCurrentPage - 1) * this.masterPageSize;
    const end = start + this.masterPageSize;
    const pageItems = listToRender.slice(start, end);

    let html = '';
    pageItems.forEach(item => {
      const cat = item.category || 'Mechanical Parts';
      const catColor = cat === 'Consumables' ? '#ffb84d' : (cat === 'Electrical Parts' ? '#a78bfa' : (cat === 'Lubes' ? '#e11d48' : '#29d391'));

      html += `
        <tr>
          <td style="font-weight: 850; color: #38bdf8;">${item.aggregate || 'GENERAL'}</td>
          <td style="font-weight: 700; color: #a78bfa;">${item.subAggregate || 'GENERAL'}</td>
          <td style="font-weight: 850; color: #ffffff;">${item.component || 'UNMAPPED'}</td>
          <td style="font-weight: 850; color: ${catColor};"><span class="badge" style="background: ${catColor}20; color: ${catColor}; border: 1px solid ${catColor}40; font-size: 0.72rem; font-weight: 850;">${cat}</span></td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
    this.renderMasterPagination(listToRender.length);
  },

  renderMasterPagination(totalCount) {
    const pagContainer = document.getElementById('master-pagination');
    if (!pagContainer) return;

    const count = (typeof totalCount === 'number') ? totalCount : (this.filteredMaster ? this.filteredMaster.length : 0);
    const totalPages = Math.ceil(count / this.masterPageSize) || 1;
    if (this.masterCurrentPage > totalPages) this.masterCurrentPage = totalPages;

    const startItem = count > 0 ? (this.masterCurrentPage - 1) * this.masterPageSize + 1 : 0;
    const endItem = Math.min(this.masterCurrentPage * this.masterPageSize, count);

    pagContainer.innerHTML = `
      <div style="font-size:0.8rem; color:var(--text-muted);">
        Showing ${startItem} to ${endItem} of ${count} catalogue items
      </div>
      <div style="display:flex; gap:0.5rem;">
        <button class="btn btn-secondary" style="padding:0.25rem 0.65rem; font-size:0.75rem;" ${this.masterCurrentPage <= 1 ? 'disabled' : ''} onclick="MappingPortal.changeMasterPage(${this.masterCurrentPage - 1})">Prev</button>
        <span style="font-size:0.85rem; font-weight:700; padding: 0.2rem 0.5rem;">${this.masterCurrentPage} / ${totalPages}</span>
        <button class="btn btn-secondary" style="padding:0.25rem 0.65rem; font-size:0.75rem;" ${this.masterCurrentPage >= totalPages ? 'disabled' : ''} onclick="MappingPortal.changeMasterPage(${this.masterCurrentPage + 1})">Next</button>
      </div>
    `;
  },'''

pattern = r'  filterMasterTable\(query = ""\) \{.*?renderMasterPagination\(.*?\}\n  \},'
code_updated, count = re.subn(pattern, new_methods, code, flags=re.DOTALL)
print('Replaced count:', count)

with open('js/mapping-portal.js', 'w', encoding='utf-8') as f:
    f.write(code_updated)
