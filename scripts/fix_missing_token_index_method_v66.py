import re

def fix_missing_method():
    with open('js/data-engine.js', 'r', encoding='utf-8') as f:
        text = f.read()

    method_def = """  buildFastTokenIndexes() {
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
  },

  initDefaultRules() {"""

    if 'initDefaultRules() {' in text and 'buildFastTokenIndexes() {' not in text:
        text = text.replace('initDefaultRules() {', method_def)
        print("Added buildFastTokenIndexes method definition to js/data-engine.js")

    # Guard the invocation
    old_call = "this.buildFastTokenIndexes();"
    new_call = "if (typeof this.buildFastTokenIndexes === 'function') { this.buildFastTokenIndexes(); }"

    if old_call in text:
        text = text.replace(old_call, new_call)
        print("Guarded buildFastTokenIndexes invocation in initDefaultRules")

    with open('js/data-engine.js', 'w', encoding='utf-8') as f:
        f.write(text)

    print("js/data-engine.js updated successfully.")

if __name__ == '__main__':
    fix_missing_method()
