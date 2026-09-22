import json

def update_data_engine():
    with open('js/data-engine.js', 'r', encoding='utf-8') as f:
        text = f.read()

    # Replace bestScore >= 4 with bestScore >= 1
    old_fuzzy_check = 'if (bestEntry && bestScore >= 4)'
    new_fuzzy_check = 'if (bestEntry && bestScore >= 1)'

    if old_fuzzy_check in text:
        text = text.replace(old_fuzzy_check, new_fuzzy_check)
        print('Updated fuzzy check score threshold to >= 1')
    else:
        print('Warning: old_fuzzy_check not found')

    # Build fast token indexes method
    fast_token_code = '''
  buildFastTokenIndexes() {
    if (!this.db.aggregateMaster) return;
    if (!this.db.tokenIndex) this.db.tokenIndex = {};

    for (let entry of this.db.aggregateMaster) {
      const comp = String(entry.component || "").toUpperCase();
      const tokens = comp.split(/[^A-Z0-9]+/).filter(t => t.length >= 3);
      for (let tok of tokens) {
        if (!this.db.tokenIndex[tok]) {
          this.db.tokenIndex[tok] = entry.component;
        }
      }
    }
  },
'''

    if 'buildFastTokenIndexes()' not in text:
        text = text.replace('initDefaultRules() {', fast_token_code + '\n  initDefaultRules() {')
        print('Added buildFastTokenIndexes method')

    # Updated findColumn implementation
    new_find_column = '''findColumn(row, keywords) {
    if (!row || typeof row !== 'object') return "";
    const keys = Object.keys(row);
    for (let kw of keywords) {
      const exactKey = keys.find(k => k.trim().toLowerCase() === kw.trim().toLowerCase());
      if (exactKey && row[exactKey] !== undefined && row[exactKey] !== null && String(row[exactKey]).trim() !== "") {
        return row[exactKey];
      }
    }
    for (let kw of keywords) {
      const kwNorm = kw.toLowerCase().replace(/[^a-z0-9]/g, '');
      const foundKey = keys.find(k => k.toLowerCase().replace(/[^a-z0-9]/g, '').includes(kwNorm));
      if (foundKey && row[foundKey] !== undefined && row[foundKey] !== null && String(row[foundKey]).trim() !== "") {
        return row[foundKey];
      }
    }
    return "";
  },'''

    start_fc = text.find('findColumn(row, keywords) {')
    end_fc = text.find('// Parse Raw Uploaded', start_fc)
    if start_fc != -1 and end_fc != -1:
        text = text[:start_fc] + new_find_column + '\n\n  ' + text[end_fc:]
        print('Updated findColumn implementation')

    # Updated keywords in processSalesUpload
    old_keywords = "const partKeywords = ['part', 'itemcode', 'code', 'sku', 'material', 'productno', 'article', 'lncode'];\n    const descKeywords = ['desc', 'itemname', 'name', 'detail', 'specification', 'title'];"

    new_keywords = "const partKeywords = ['partno', 'part number', 'part_number', 'itemcode', 'item code', 'item_code', 'manpart', 'material', 'sku', 'productno', 'article', 'lncode', 'part'];\n    const descKeywords = ['description', 'item description', 'item_description', 'part description', 'part_description', 'itemdesc', 'item desc', 'itemname', 'item name', 'item_name', 'desc', 'detail', 'specification', 'title'];"

    if old_keywords in text:
        text = text.replace(old_keywords, new_keywords)
        print('Updated keywords list in processSalesUpload')

    with open('js/data-engine.js', 'w', encoding='utf-8') as f:
        f.write(text)

    print('js/data-engine.js updated successfully!')

if __name__ == '__main__':
    update_data_engine()
