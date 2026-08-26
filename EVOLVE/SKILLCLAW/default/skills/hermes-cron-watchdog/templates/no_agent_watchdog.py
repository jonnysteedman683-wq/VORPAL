"""Zero-token no_agent cron watchdog wrapper template.

Copy and adapt. Runs a deterministic task script via the SAME interpreter the
wrapper runs under (sys.executable), prints NOTHING on success (no_agent cron
delivers nothing -> zero tokens), prints a failure report on non-zero/timeout,
and always writes a full audit log to ~/.hermes/cron_log/.
"""
import datetime
import os
import subprocess
import sys

REPO = r"C:\path\to\your\repo"          # change: chdir target
TASK_SCRIPT = "your_task.py"            # change: the task to run
LOG_DIR = os.path.join(os.path.expanduser("~"), ".hermes", "cron_log")
TIMEOUT_S = 1200                        # generous; tune to the task

os.chdir(REPO)

try:
    proc = subprocess.run(
        [sys.executable, TASK_SCRIPT],  # sys.executable, NOT bare 'python'
        capture_output=True,
        text=True,
        timeout=TIMEOUT_S,
        encoding="utf-8",
        errors="replace",
    )
except subprocess.TimeoutExpired as exc:
    print(f"[WATCHDOG TIMEOUT (> {TIMEOUT_S}s)]")
    print((exc.stdout or "")[-2000:])
    print((exc.stderr or "")[-2000:])
    sys.exit(1)

os.makedirs(LOG_DIR, exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
log_path = os.path.join(LOG_DIR, f"{os.path.basename(TASK_SCRIPT)}-{stamp}.log")
with open(log_path, "w", encoding="utf-8") as fh:
    fh.write(proc.stdout)
    fh.write("\n--- STDERR ---\n")
    fh.write(proc.stderr)

if proc.returncode == 0:
    # Success -> silent. Full log written for audit; cron delivers nothing.
    sys.exit(0)

# Failure -> emit a report so the no_agent cron delivers an alert.
print(f"[WATCHDOG FAILED rc={proc.returncode}] log={log_path}")
print((proc.stdout or "")[-3000:])
print((proc.stderr or "")[-2000:])
sys.exit(proc.returncode)
