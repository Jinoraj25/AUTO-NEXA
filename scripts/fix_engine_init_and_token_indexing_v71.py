import re, os

print("=== Fixing DataEngine Init and Token Index Building (v71) ===")

data_engine_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\data-engine.js"
with open(data_engine_path, "r", encoding="utf-8") as f:
    de_code = f.read()

# 1. Ensure buildFastTokenIndexes() is called at the end of init()
old_init_tail = """    if (window.MappingPortal && typeof window.MappingPortal.renderAggregateMasterTable === 'function') {
      window.MappingPortal.filteredMaster = [...this.db.aggregateMaster];
      window.MappingPortal.renderAggregateMasterTable();
    }

    // Non-blocking background lazy-load for 360,000 partNoLookup table
    setTimeout(() => this.lazyLoadPartLookup(), 300);
  },"""

new_init_tail = """    if (typeof this.buildFastTokenIndexes === 'function') {
      this.buildFastTokenIndexes();
    }

    if (window.MappingPortal && typeof window.MappingPortal.renderAggregateMasterTable === 'function') {
      window.MappingPortal.filteredMaster = [...this.db.aggregateMaster];
      window.MappingPortal.renderAggregateMasterTable();
    }

    // Non-blocking background lazy-load for 360,000 partNoLookup table
    setTimeout(() => this.lazyLoadPartLookup(), 300);
  },"""

if old_init_tail in de_code:
    de_code = de_code.replace(old_init_tail, new_init_tail, 1)
    print("Added buildFastTokenIndexes() call into DataEngine.init()")

# 2. Update buildFastTokenIndexes to exclude stop words
old_build_tokens = """  buildFastTokenIndexes() {
    if (!this.db || !this.db.aggregateMaster) return;
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
  },"""

new_build_tokens = """  buildFastTokenIndexes() {
    if (!this.db || !this.db.aggregateMaster) return;
    if (!this.db.tokenIndex) this.db.tokenIndex = {};

    const STOP_WORDS = new Set(['LH', 'RH', 'SET', 'KIT', 'FOR', 'AND', 'WITH', 'TYPE', 'STD', 'ASSY', 'NO', 'OFF', 'PCS', 'BLK', 'RED', 'BLUE', 'TYPE1', 'TYPE2', 'ECO', 'NEW', 'OLD', 'GENUINE', 'OEN', 'OEM', 'CAR', 'BLACK', 'WHITE', 'SIDE', 'FRONT', 'REAR', 'INNER', 'OUTER', 'TOP', 'BOTTOM', 'UPPER', 'LOWER']);

    for (let entry of this.db.aggregateMaster) {
      const comp = String(entry.component || "").toUpperCase();
      const tokens = comp.split(/[^A-Z0-9]+/).filter(t => t.length >= 3 && !STOP_WORDS.has(t));
      for (let tok of tokens) {
        if (!this.db.tokenIndex[tok]) {
          this.db.tokenIndex[tok] = entry.component;
        }
      }
    }
  },"""

if old_build_tokens in de_code:
    de_code = de_code.replace(old_build_tokens, new_build_tokens, 1)
    print("Updated buildFastTokenIndexes() to filter out STOP_WORDS")

with open(data_engine_path, "w", encoding="utf-8") as f:
    f.write(de_code)

# 3. Update js/mapping-portal.js to call buildFastTokenIndexes() on upload
mp_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\mapping-portal.js"
with open(mp_path, "r", encoding="utf-8") as f:
    mp_code = f.read()

old_mp_init_call = """      if (typeof window.DataEngine.initDefaultRules === 'function' && (!window.DataEngine.db || !window.DataEngine.db.aggregateMaster)) {
        window.DataEngine.initDefaultRules();
      }"""

new_mp_init_call = """      if (typeof window.DataEngine.initDefaultRules === 'function' && (!window.DataEngine.db || !window.DataEngine.db.aggregateMaster)) {
        window.DataEngine.initDefaultRules();
      }
      if (typeof window.DataEngine.buildFastTokenIndexes === 'function') {
        window.DataEngine.buildFastTokenIndexes();
      }"""

if old_mp_init_call in mp_code:
    mp_code = mp_code.replace(old_mp_init_call, new_mp_init_call, 1)
    print("Added buildFastTokenIndexes() call into handleFileUpload in mapping-portal.js")

with open(mp_path, "w", encoding="utf-8") as f:
    f.write(mp_code)

print("Done applying DataEngine init and token indexing fixes!")
