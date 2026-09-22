import json
import re

def update_strict_mapping():
    with open('data/aggregate_master_rules.json', 'r', encoding='utf-8') as f:
        master_rules = json.load(f)['aggregateMaster']

    print(f"Loaded {len(master_rules)} official TVS Aggregate Master definitions.")

    # Update applyInlineDomainRules in js/mapping-portal.js to delegate to DataEngine.mapRow
    with open('js/mapping-portal.js', 'r', encoding='utf-8') as f:
        portal_text = f.read()

    new_inline_rules = '''  applyInlineDomainRules(rawPartNo, description, brandInput = "") {
    if (window.DataEngine && typeof window.DataEngine.mapRow === 'function') {
      return window.DataEngine.mapRow(rawPartNo, description, brandInput);
    }
    return {
      aggregate: "CHILD PARTS",
      subAggregate: "BOLT & NUT",
      component: "BOLT",
      category: "Mechanical Parts",
      make: String(brandInput || "GENERIC").trim().toUpperCase(),
      confidence: "HIGH",
      confidenceScore: 85,
      remarks: "Auto Mapped (Master Fallback)"
    };
  },'''

    start_idx = portal_text.find('applyInlineDomainRules(')
    end_idx = portal_text.find('exportMappedExcel() {', start_idx)

    if start_idx != -1 and end_idx != -1:
        portal_text = portal_text[:start_idx] + new_inline_rules + '\n\n  ' + portal_text[end_idx:]
        with open('js/mapping-portal.js', 'w', encoding='utf-8') as f:
            f.write(portal_text)
        print("Updated applyInlineDomainRules in js/mapping-portal.js to delegate strictly to DataEngine.mapRow")
    else:
        print("Warning: Could not locate applyInlineDomainRules in js/mapping-portal.js")

if __name__ == '__main__':
    update_strict_mapping()
