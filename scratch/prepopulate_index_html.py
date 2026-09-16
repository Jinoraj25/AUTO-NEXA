import json

with open('data/aggregate_master_rules.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

rules = data.get('aggregateMaster', [])
print(f"Loaded {len(rules)} rules to pre-render into index.html")

page_items = rules[:10]
tbody_html = ''
for item in page_items:
    cat = item.get('category', 'Mechanical Parts')
    catColor = '#ffb84d' if cat == 'Consumables' else ('#a78bfa' if cat == 'Electrical Parts' else ('#e11d48' if cat == 'Lubes' else '#29d391'))
    tbody_html += f'''
                <tr>
                  <td style="font-weight: 850; color: #38bdf8;">{item.get('aggregate', 'GENERAL')}</td>
                  <td style="font-weight: 700; color: #a78bfa;">{item.get('subAggregate', 'GENERAL')}</td>
                  <td style="font-weight: 850; color: #ffffff;">{item.get('component', 'UNMAPPED')}</td>
                  <td style="font-weight: 850; color: {catColor};"><span class="badge" style="background: {catColor}20; color: {catColor}; border: 1px solid {catColor}40; font-size: 0.72rem; font-weight: 850;">{cat}</span></td>
                </tr>'''

pagination_html = f'''
              <div style="font-size:0.8rem; color:var(--text-muted);">
                Showing 1 to 10 of {len(rules)} catalogue items
              </div>
              <div style="display:flex; gap:0.5rem;">
                <button class="btn btn-secondary" style="padding:0.25rem 0.65rem; font-size:0.75rem;" disabled onclick="MappingPortal.changeMasterPage(1)">Prev</button>
                <span style="font-size:0.85rem; font-weight:700; padding: 0.2rem 0.5rem;">1 / {((len(rules)-1)//10)+1}</span>
                <button class="btn btn-secondary" style="padding:0.25rem 0.65rem; font-size:0.75rem;" onclick="MappingPortal.changeMasterPage(2)">Next</button>
              </div>'''

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace tbody
import re
pattern_tbody = r'<tbody id="master-rules-list">.*?</tbody>'
replacement_tbody = f'<tbody id="master-rules-list">{tbody_html}\n              </tbody>'
html_updated, c1 = re.subn(pattern_tbody, replacement_tbody, html, flags=re.DOTALL)
print("Replaced tbody in index.html:", c1)

# Replace pagination
pattern_pag = r'<div id="master-pagination" class="table-toolbar">.*?</div>'
replacement_pag = f'<div id="master-pagination" class="table-toolbar">{pagination_html}\n            </div>'
html_updated, c2 = re.subn(pattern_pag, replacement_pag, html_updated, flags=re.DOTALL)
print("Replaced pagination in index.html:", c2)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_updated)

print("Pre-populated index.html statically with 10 master rule rows and pagination controls!")
