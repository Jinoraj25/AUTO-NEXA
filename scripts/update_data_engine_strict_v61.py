import json

def update_data_engine_strict():
    with open('js/data-engine.js', 'r', encoding='utf-8') as f:
        text = f.read()

    old_fallback_code = '''    // Strategy 5: 100% Coverage Master Fallback
    const fallbackEntry = findInMaster("HARDWARE & FASTENERS") || {
      aggregate: "CHILD PARTS",
      subAggregate: "BOLT & NUT",
      component: "HARDWARE & FASTENERS",
      category: "Mechanical Parts"
    };'''

    new_fallback_code = '''    // Strategy 5: 100% Coverage Master Fallback
    const fallbackEntry = findInMaster("BOLT") || findInMaster("NUT") || {
      aggregate: "CHILD PARTS",
      subAggregate: "BOLT & NUT",
      component: "BOLT",
      category: "Mechanical Parts"
    };'''

    if old_fallback_code in text:
        text = text.replace(old_fallback_code, new_fallback_code)
        print("Updated Strategy 5 fallback in js/data-engine.js to use official master component 'BOLT'")
    else:
        print("Warning: old_fallback_code not found in js/data-engine.js")

    with open('js/data-engine.js', 'w', encoding='utf-8') as f:
        f.write(text)

if __name__ == '__main__':
    update_data_engine_strict()
