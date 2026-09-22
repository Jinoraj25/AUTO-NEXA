import os, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

git_exe = r"C:\Users\SM0237\AppData\Local\Programs\Git\cmd\git.exe"

def run(args):
    cmd = [git_exe] + args
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"=== {' '.join(cmd)} ===")
    print("STDOUT:", res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)

run(['status'])
run(['add', '.'])
run(['commit', '-m', 'Fix unique aggregate counting to map across 15+ aggregates and enable high performance UTF8 BOM CSV export for 38000+ rows v60.0.0'])
run(['push', 'origin', 'main'])
