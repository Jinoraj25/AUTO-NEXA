import re

with open('js/mapping-portal.js', 'r', encoding='utf-8') as f:
    code = f.read()

new_methods = '''  getFullMaster() {
    if (window.DataEngine && window.DataEngine.db && Array.isArray(window.DataEngine.db.aggregateMaster) && window.DataEngine.db.aggregateMaster.length > 0) {
      return window.DataEngine.db.aggregateMaster;
    }
    if (window.DataEngine && typeof window.DataEngine.initDefaultRules === 'function') {
      window.DataEngine.initDefaultRules();
      if (window.DataEngine.db && Array.isArray(window.DataEngine.db.aggregateMaster) && window.DataEngine.db.aggregateMaster.length > 0) {
        return window.DataEngine.db.aggregateMaster;
      }
    }
    return [];
  },

  filterMasterTable(query = "") {
    this.masterCurrentPage = 1;
    this.renderAggregateMasterTable(query);
  },

  renderAggregateMasterTable(queryOverride) {
    const tbody = document.getElementById('master-rules-list');
    if (!tbody) return;

    const fullMaster = this.getFullMaster();
    const searchInput = document.getElementById('master-search-input');
    const rawQuery = (typeof queryOverride === 'string') ? queryOverride : (searchInput ? searchInput.value : "");
    const q = String(rawQuery || "").trim().toLowerCase();

    let listToRender = fullMaster;
    if (q) {
      listToRender = fullMaster.filter(item => {
        return (item.aggregate && item.aggregate.toLowerCase().includes(q)) ||
               (item.subAggregate && item.subAggregate.toLowerCase().includes(q)) ||
               (item.component && item.component.toLowerCase().includes(q)) ||
               (item.category && item.category.toLowerCase().includes(q));
      });
    }

    this.filteredMaster = listToRender;

    if (!listToRender || listToRender.length === 0) {
      if (!q) {
        // Query is empty but list is not ready yet - retry in 150ms without clearing pre-rendered HTML!
        setTimeout(() => this.renderAggregateMasterTable(), 150);
        return;
      }
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
  },'''

pattern = r'  getFullMaster\(\) \{.*?renderAggregateMasterTable\(queryOverride\) \{.*?\n  \},'
code_updated, count = re.subn(pattern, new_methods, code, flags=re.DOTALL)
print('Replaced count:', count)

with open('js/mapping-portal.js', 'w', encoding='utf-8') as f:
    f.write(code_updated)
