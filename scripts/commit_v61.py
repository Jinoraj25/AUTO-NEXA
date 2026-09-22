import subprocess
import os

git_exe = r"C:\Users\SM0237\AppData\Local\Programs\Git\cmd\git.exe"

def git_commit_and_push():
    print("Checking git status using", git_exe)
    st = subprocess.run([git_exe, "status", "--porcelain"], capture_output=True, text=True)
    print("Git status output:\n", st.stdout)

    print("Adding all files...")
    subprocess.run([git_exe, "add", "."], check=True)

    print("Committing v61.0.0 mapping fixes...")
    msg = "Fix catalogue mapping logic: embed 923 TVS Aggregate Master rules, fix 1-aggregate bug, enable instant CSV stream download"
    subprocess.run([git_exe, "commit", "-m", msg], check=False)

    print("Pushing to GitHub origin main...")
    push_res = subprocess.run([git_exe, "push", "origin", "main"], capture_output=True, text=True)
    print("Git push stdout:\n", push_res.stdout)
    print("Git push stderr:\n", push_res.stderr)

if __name__ == '__main__':
    git_commit_and_push()
