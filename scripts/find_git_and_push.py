import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

possible_paths = [
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Program Files (x86)\Git\cmd\git.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Git\cmd\git.exe"),
    os.path.expanduser(r"~\AppData\Local\GitHubDesktop\bin\git.exe")
]

git_cmd = "git"
for p in possible_paths:
    if os.path.exists(p):
        git_cmd = f'"{p}"'
        print(f"Found Git at: {p}")
        break

print(f"Using Git Command: {git_cmd}")

# Test git version
try:
    res = subprocess.run(f"{git_cmd} --version", shell=True, capture_output=True, text=True)
    print("Git Version Output:", res.stdout.strip())
except Exception as e:
    print("Git version test failed:", e)

# Run git status
try:
    res = subprocess.run(f"{git_cmd} status", shell=True, capture_output=True, text=True)
    print("\n--- Git Status Output ---")
    print(res.stdout)
    if res.stderr:
        print("Git Status Stderr:", res.stderr)
except Exception as e:
    print("Git status failed:", e)
