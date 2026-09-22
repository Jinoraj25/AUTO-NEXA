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
run(['commit', '-m', 'Add exportMappedExcel download method and fast API parsing for large sales files v59.0.0'])
run(['push', 'origin', 'main'])
