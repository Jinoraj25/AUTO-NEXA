import json
import re

def sanitize():
    # Load official TVS master rules
    with open('data/aggregate_master_rules.json', 'r', encoding='utf-8') as f:
        master_rules = json.load(f)['aggregateMaster']

    master_triples = set((m['aggregate'], m['subAggregate'], m['component']) for m in master_rules)

    print(f"Total TVS Aggregate Master Rule Triples: {len(master_triples)}")

    # Sanitize js/mapping-portal.js
    with open('js/mapping-portal.js', 'r', encoding='utf-8') as f:
        portal_text = f.read()

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

    with open('js/mapping-portal.js', 'w', encoding='utf-8') as f:
        f.write(portal_text)

    # Sanitize js/data-engine.js
    with open('js/data-engine.js', 'r', encoding='utf-8') as f:
        de_text = f.read()

    for old_s, new_s in replacements.items():
        if old_s in de_text:
            de_text = de_text.replace(old_s, new_s)
            print(f"Replaced {old_s} -> {new_s} in data-engine.js")

    with open('js/data-engine.js', 'w', encoding='utf-8') as f:
        f.write(de_text)

    print("Sanitization completed successfully.")

if __name__ == '__main__':
    sanitize()
