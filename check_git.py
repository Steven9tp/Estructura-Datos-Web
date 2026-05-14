import subprocess

def check_git():
    try:
        status = subprocess.run(['git', 'status'], capture_output=True, text=True)
        log = subprocess.run(['git', 'log', '-n', '3', '--oneline'], capture_output=True, text=True)
        remote = subprocess.run(['git', 'ls-remote', 'origin', 'main'], capture_output=True, text=True)
        local = subprocess.run(['git', 'rev-parse', 'main'], capture_output=True, text=True)
        
        with open('git_diag.txt', 'w', encoding='utf-8') as f:
            f.write("--- STATUS ---\n" + status.stdout + "\n")
            f.write("--- LOG ---\n" + log.stdout + "\n")
            f.write("--- REMOTE ---\n" + remote.stdout + "\n")
            f.write("--- LOCAL ---\n" + local.stdout + "\n")
            f.write("--- ERRORS ---\n" + status.stderr + log.stderr + remote.stderr + local.stderr)
            
    except Exception as e:
        with open('git_diag.txt', 'w', encoding='utf-8') as f:
            f.write(f"Error: {e}")

if __name__ == '__main__':
    check_git()
