import json, re

with open('data/aggregate_master_rules.json', 'r', encoding='utf-8') as f:
    rules_obj = json.load(f)

rules = rules_obj.get('aggregateMaster', [])
formatted_json = json.dumps(rules, indent=2)

with open('js/data-engine.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace aggregateMaster array at top of file
pattern_db = r'aggregateMaster:\s*\[\s*\{.*?\}\s*\]'
replacement_db = f'aggregateMaster: {formatted_json}'

code_updated, c1 = re.subn(pattern_db, replacement_db, code, count=1, flags=re.DOTALL)
print('Replaced aggregateMaster at top:', c1)

# Replace initDefaultRules array
pattern_init = r'initDefaultRules\(\)\s*\{\s*this\.db\.aggregateMaster\s*=\s*\[\s*\{.*?\}\s*\];'
replacement_init = f'initDefaultRules() {{\n    this.db.aggregateMaster = {formatted_json};'

code_updated, c2 = re.subn(pattern_init, replacement_init, code_updated, count=1, flags=re.DOTALL)
print('Replaced initDefaultRules array:', c2)

with open('js/data-engine.js', 'w', encoding='utf-8') as f:
    f.write(code_updated)

print('Updated js/data-engine.js with 923 rules!')
