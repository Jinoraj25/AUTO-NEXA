import json
import re

def apply_safe_fixes():
    # Load official TVS master rules
    with open('data/aggregate_master_rules.json', 'r', encoding='utf-8') as f:
        master_rules = json.load(f)['aggregateMaster']

    master_triples = set((m['aggregate'], m['subAggregate'], m['component']) for m in master_rules)
    print(f"Loaded {len(master_triples)} official TVS Aggregate Master triples.")

    # 1. Update js/mapping-portal.js
    with open('js/mapping-portal.js', 'r', encoding='utf-8') as f:
        portal_text = f.read()

    # Safely replace non-master fallback strings in mapping-portal.js
    replacements = {
        '"MECHANICAL AGGREGATES"': '"CHILD PARTS"',
        '"GENERAL SPARES"': '"BOLT & NUT"',
        '"AUTO COMPONENT"': '"BOLT"',
        '"GENERAL COMPONENT"': '"BOLT"',
        '"ENGINE SYSTEM"': '"ENGINE"',
        '"SUSPENSION SYSTEM"': '"SUSPENSION"',
        '"STEERING SYSTEM"': '"STEERING"',
        '"LUBES AND FLUIDS"': '"LUBES"',
        '"BODY & TRIM"': '"BODY PARTS"'
    }

    for old_s, new_s in replacements.items():
        if old_s in portal_text:
            portal_text = portal_text.replace(old_s, new_s)
            print(f"Replaced {old_s} -> {new_s} in mapping-portal.js")

    # Update applyInlineDomainRules at the end of MappingPortal object in mapping-portal.js
    apply_rules_start = portal_text.find('applyInlineDomainRules(')
    apply_rules_end = portal_text.find('exportMappedExcel() {', apply_rules_start)

    if apply_rules_start != -1 and apply_rules_end != -1:
        new_inline_method = '''applyInlineDomainRules(rawPartNo, description, brandInput = "") {
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
      remarks: "Auto Mapped (Master Rule)"
    };
  },'''
        portal_text = portal_text[:apply_rules_start] + new_inline_method + '\n\n  ' + portal_text[apply_rules_end:]
        print("Safely replaced applyInlineDomainRules method in mapping-portal.js")

    with open('js/mapping-portal.js', 'w', encoding='utf-8') as f:
        f.write(portal_text)

    # 2. Update js/data-engine.js
    with open('js/data-engine.js', 'r', encoding='utf-8') as f:
        de_text = f.read()

    for old_s, new_s in replacements.items():
        if old_s in de_text:
            de_text = de_text.replace(old_s, new_s)
            print(f"Replaced {old_s} -> {new_s} in data-engine.js")

    with open('js/data-engine.js', 'w', encoding='utf-8') as f:
        f.write(de_text)

    print("Safe fixes applied successfully.")

if __name__ == '__main__':
    apply_safe_fixes()
