import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "<script" in line:
        print(f"Line {idx}: {line.strip()}")
        end_idx = min(len(lines), idx + 45)
        for j in range(idx, end_idx):
            if "</script>" in lines[j]:
                print(f"   L{j+1}: {lines[j].strip()}")
                break
            print(f"   L{j+1}: {lines[j].strip()}")
        print("-" * 50)
