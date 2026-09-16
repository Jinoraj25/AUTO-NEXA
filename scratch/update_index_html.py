with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Aggregate Master header in index.html
old_master_header = '''            <div class="header-right-actions">
              <input type="text" id="master-search-input" placeholder="Search Master Rules (Aggregate, Sub-Aggregate, Component)..." oninput="MappingPortal.filterMasterTable(this.value)" style="background: rgba(255, 255, 255, 0.06); border: 1.5px solid rgba(56, 189, 248, 0.35); border-radius: 9px; padding: 0.5rem 1rem; color: #fff; font-size: 0.85rem; width: 320px;">
            </div>'''

new_master_header = '''            <div class="header-right-actions" style="display: flex; gap: 0.65rem; align-items: center;">
              <input type="text" id="master-search-input" placeholder="Search Master Rules (Aggregate, Sub-Aggregate, Component)..." oninput="MappingPortal.filterMasterTable(this.value)" style="background: rgba(255, 255, 255, 0.06); border: 1.5px solid rgba(56, 189, 248, 0.35); border-radius: 9px; padding: 0.5rem 1rem; color: #fff; font-size: 0.85rem; width: 320px;">
              <button type="button" class="btn btn-secondary" onclick="document.getElementById('master-rules-file-input').click();" style="padding: 0.5rem 0.85rem; font-size: 0.8rem; font-weight: 700; border-radius: 9px; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8;">📤 Upload Master Rules Excel</button>
              <input type="file" id="master-rules-file-input" accept=".xlsx,.xls,.csv" style="display: none;" onchange="MappingPortal.handleMasterRulesUpload(this.files[0])">
            </div>'''

html_updated = html.replace(old_master_header, new_master_header)

# 2. Add inventory pagination div in index.html
old_table_end = '''            <tbody id="inventory-table-body">
              <!-- Populated via inventory-portal.js -->
            </tbody>
          </table>
        </div>'''

new_table_end = '''            <tbody id="inventory-table-body">
              <!-- Populated via inventory-portal.js -->
            </tbody>
          </table>
          <div id="inventory-pagination" class="table-toolbar" style="display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1rem; background: rgba(15, 23, 42, 0.6); border-top: 1px solid rgba(255, 255, 255, 0.08);">
            <!-- Inventory search grid pagination -->
          </div>
        </div>'''

html_updated = html_updated.replace(old_table_end, new_table_end)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_updated)

print("Updated index.html with Master Rules upload button and inventory pagination container!")
