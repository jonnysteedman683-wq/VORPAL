"""MARKUS OS auto-upgrade watchdog (zero-token cron script).

Runs the full MARKUS upgrade cycle (markus_upgrade_start.py). Prints NOTHING on
success (cron stays silent, no delivery); on failure prints a report so the cron
delivers an alert. Exit code mirrors the cycle's rc.

Script location: AppData\\Local\\hermes\\scripts\\markus_auto_upgrade.py
Managed by: Hermes cron job 'markus-auto-upgrade' (no_agent=True).
"""
import os
import subprocess
import sys
import datetime

REPO = r"C:\Users\jonny\OneDrive\Desktop\MARKUS-OS"
LOG_DIR = os.path.join(os.path.expanduser("~"), ".hermes", "cron_log")

os.chdir(REPO)

try:
    proc = subprocess.run(
        [sys.executable, "markus_upgrade_start.py"],
        capture_output=True,
        text=True,
        timeout=1200,
        encoding="utf-8",
        errors="replace",
    )
except subprocess.TimeoutExpired as exc:
    print("[MARKUS AUTO-UPGRADE TIMEOUT (>1200s)]")
    print((exc.stdout or "")[-2000:])
    print((exc.stderr or "")[-2000:])
    sys.exit(1)

os.makedirs(LOG_DIR, exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
log_path = os.path.join(LOG_DIR, f"auto-upgrade-{stamp}.log")
with open(log_path, "w", encoding="utf-8") as fh:
    fh.write(proc.stdout)
    fh.write("\n--- STDERR ---\n")
    fh.write(proc.stderr)

if proc.returncode == 0:
    # Success -> silent. Full log already written for audit.
    sys.exit(0)

# Failure -> emit report so the cron delivers an alert.
print(f"[MARKUS AUTO-UPGRADE FAILED rc={proc.returncode}] log={log_path}")
print((proc.stdout or "")[-3000:])
print((proc.stderr or "")[-2000:])
sys.exit(proc.returncode)
