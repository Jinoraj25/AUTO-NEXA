import re

with open('js/data-engine.js', 'r', encoding='utf-8') as f:
    code = f.read()

new_init = '''  async init() {
    if (!this.db.aggregateMaster || this.db.aggregateMaster.length === 0) {
      this.initDefaultRules();
    }
    try {
      console.log("DataEngine: Loading fast aggregate master rules...");
      let res = await fetch('data/aggregate_master_rules.json');
      if (!res.ok) res = await fetch('aggregate_master_rules.json');
      if (!res.ok) res = await fetch('/api/master_rules');

      if (res.ok) {
        const rulesData = await res.json();
        if (rulesData && Array.isArray(rulesData.aggregateMaster) && rulesData.aggregateMaster.length > 0) {
          this.db.aggregateMaster = rulesData.aggregateMaster;
          this.isLoaded = true;
          console.log(`DataEngine: Success! Instant loaded ${this.db.aggregateMaster.length} Aggregate Master rules.`);
        }
      }
    } catch (e) {
      console.warn("DataEngine fast rules notice, using defaults:", e);
    }

    if (!this.db.aggregateMaster || this.db.aggregateMaster.length === 0) {
      this.initDefaultRules();
    }

    if (window.MappingPortal && typeof window.MappingPortal.renderAggregateMasterTable === 'function') {
      window.MappingPortal.filteredMaster = [...this.db.aggregateMaster];
      window.MappingPortal.renderAggregateMasterTable();
    }

    // Non-blocking background lazy-load for 360,000 partNoLookup table
    setTimeout(() => this.lazyLoadPartLookup(), 300);
  },'''

pattern = r'  async init\(\) \{.*?setTimeout\(\(\) => this\.lazyLoadPartLookup\(\), 300\);\n  \},'
code_updated, count = re.subn(pattern, new_init, code, flags=re.DOTALL)
print('Replaced init count:', count)

with open('js/data-engine.js', 'w', encoding='utf-8') as f:
    f.write(code_updated)
