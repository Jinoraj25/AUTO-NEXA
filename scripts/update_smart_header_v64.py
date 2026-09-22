import os

def update_server_and_js():
    # 1. Update server.py for automatic header promotion
    with open('server.py', 'r', encoding='utf-8') as f:
        server_text = f.read()

    old_df_clean = """                if df is not None:
                    df = df.fillna('')
                    records = df.to_dict(orient='records')"""

    new_df_clean = """                if df is not None:
                    # Smart header row promotion for files with top title/blank rows or Unnamed columns
                    if any('Unnamed' in str(c) for c in df.columns):
                        for idx, row in df.head(5).iterrows():
                            vals = [str(v).lower().replace(' ', '').replace('_', '') for v in row.values if pd.notna(v)]
                            if any(kw in v for v in vals for kw in ['partno', 'partnumber', 'itemdesc', 'itemdescription', 'itemcode', 'itemname', 'description', 'partdescription', 'itemdesc']):
                                new_cols = [str(v).strip() if pd.notna(v) and str(v).strip() else f'Col_{i}' for i, v in enumerate(row.values)]
                                df = df.iloc[idx+1:].copy()
                                df.columns = new_cols
                                break

                    df = df.fillna('')
                    records = df.to_dict(orient='records')"""

    if old_df_clean in server_text:
        server_text = server_text.replace(old_df_clean, new_df_clean)
        with open('server.py', 'w', encoding='utf-8') as f:
            f.write(server_text)
        print("Successfully updated server.py with smart header row promotion.")
    else:
        print("Warning: old_df_clean not found in server.py")

    # 2. Update js/data-engine.js for smart content inspection
    with open('js/data-engine.js', 'r', encoding='utf-8') as f:
        de_text = f.read()

    smart_inspector_js = """  inspectColumnsByContent(rawRows) {
    if (!Array.isArray(rawRows) || rawRows.length === 0) return { partCol: null, descCol: null };
    const sample = rawRows.slice(0, 10);
    const keys = Object.keys(sample[0]);

    let partCol = null;
    let descCol = null;

    // Phase 1: Header values inside first 3 data rows
    for (let r of sample.slice(0, 3)) {
      for (let k of keys) {
        const vStr = String(r[k] || '').toLowerCase().replace(/[^a-z0-9]/g, '');
        if (!partCol && (vStr.includes('partno') || vStr.includes('partnumber') || vStr.includes('itemcode') || vStr.includes('partcode') || vStr === 'part')) {
          partCol = k;
        }
        if (!descCol && (vStr.includes('description') || vStr.includes('itemdesc') || vStr.includes('itemdescription') || vStr.includes('partdesc') || vStr.includes('itemname'))) {
          descCol = k;
        }
      }
    }

    // Phase 2: Content inspection of actual data values
    if (!partCol || !descCol) {
      for (let k of keys) {
        const vals = sample.slice(1).map(r => String(r[k] || '').trim()).filter(v => v.length > 0);
        if (vals.length === 0) continue;

        const isPartNoPattern = vals.every(v => /^[A-Z0-9\-\.\/]{4,30}$/i.test(v) && /\d/.test(v));
        const isDescPattern = vals.some(v => v.includes(' ') || v.length > 10);

        if (isPartNoPattern && !partCol) {
          partCol = k;
        } else if (isDescPattern && !descCol && k !== partCol) {
          descCol = k;
        }
      }
    }

    return { partCol, descCol };
  },"""

    if 'inspectColumnsByContent(' not in de_text:
        find_col_idx = de_text.find('findColumn(row, keywords) {')
        if find_col_idx != -1:
            de_text = de_text[:find_col_idx] + smart_inspector_js + '\n\n  ' + de_text[find_col_idx:]
            print("Added inspectColumnsByContent method to js/data-engine.js")

    # Update processSalesUpload to use inspectColumnsByContent
    old_process = """      let partNo = this.findColumn(row, partKeywords);
      let desc = this.findColumn(row, descKeywords);"""

    new_process = """      const inspected = (idx === 0) ? this.inspectColumnsByContent(rawRows) : (this._lastInspected || {});
      if (idx === 0) this._lastInspected = inspected;

      let partNo = this.findColumn(row, partKeywords) || (inspected.partCol ? row[inspected.partCol] : "");
      let desc = this.findColumn(row, descKeywords) || (inspected.descCol ? row[inspected.descCol] : "");"""

    if old_process in de_text:
        de_text = de_text.replace(old_process, new_process)
        print("Updated processSalesUpload in js/data-engine.js to use content inspection fallback.")

    with open('js/data-engine.js', 'w', encoding='utf-8') as f:
        f.write(de_text)

    print("Smart header & content inspector update completed.")

if __name__ == '__main__':
    update_server_and_js()
