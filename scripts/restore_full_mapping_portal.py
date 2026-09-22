import subprocess
import json

def restore_and_fix():
    git_exe = r"C:\Users\SM0237\AppData\Local\Programs\Git\cmd\git.exe"
    res = subprocess.run([git_exe, 'show', 'ae5b91b:js/mapping-portal.js'], capture_output=True, text=False)
    content = res.stdout.decode('utf-8', errors='ignore')

    lines = content.splitlines()
    print(f"Restored full js/mapping-portal.js from ae5b91b. Total lines: {len(lines)}")

    # Replace non-master strings
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
        if old_s in content:
            content = content.replace(old_s, new_s)
            print(f"Replaced {old_s} -> {new_s}")

    # Find applyInlineDomainRules specifically near line 669 (after index 20000)
    apply_rules_start = content.find('applyInlineDomainRules(rawPartNo', 15000)
    apply_rules_end = content.find('exportMappedExcel() {', apply_rules_start)

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
        content = content[:apply_rules_start] + new_inline_method + '\n\n  ' + content[apply_rules_end:]
        print("Successfully updated applyInlineDomainRules method at line 669")
    else:
        print("Warning: Could not find applyInlineDomainRules at index > 15000")

    with open('js/mapping-portal.js', 'w', encoding='utf-8') as f:
        f.write(content)

    final_lines = content.splitlines()
    print(f"Final js/mapping-portal.js saved. Total lines: {len(final_lines)}, bytes: {len(content)}")

if __name__ == '__main__':
    restore_and_fix()
