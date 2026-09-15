import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

git_cmd = r'"C:\Users\SM0237\AppData\Local\Programs\Git\cmd\git.exe"'

print("=== 1. Staging All Changes ===")
res1 = subprocess.run(f"{git_cmd} add .", shell=True, capture_output=True, text=True)
print(res1.stdout)
if res1.stderr:
    print("Add Stderr:", res1.stderr)

print("=== 2. Creating Git Commit ===")
commit_msg = "Complete AUTO NEXA Platform Rebuild: Scope isolation, fixed tab navigation, DOM element mapping, optimized data cache routing"
res2 = subprocess.run(f'{git_cmd} commit -m "{commit_msg}"', shell=True, capture_output=True, text=True)
print(res2.stdout)
if res2.stderr:
    print("Commit Stderr:", res2.stderr)

print("=== 3. Pushing to GitHub (origin main) ===")
res3 = subprocess.run(f"{git_cmd} push origin main", shell=True, capture_output=True, text=True)
print("Push Stdout:", res3.stdout)
if res3.stderr:
    print("Push Stderr:", res3.stderr)

print("\nGit Operation Complete!")
