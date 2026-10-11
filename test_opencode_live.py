import subprocess
import time
import sys
import os

env = os.environ.copy()
# Load .env
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k] = v.strip('"').strip("'")

if "OPENAI_API_KEY" not in env:
    print("[ERROR] OPENAI_API_KEY is not set in .env or environment.")
    sys.exit(1)

t0 = time.time()
print(f"[{time.strftime('%X')}] Starting OpenCode with openai/gpt-4o-mini...")

proc = subprocess.Popen([
    "./opencode",
    "run",
    "--auto",
    "-m", "openai/gpt-4o-mini",
    "Run ./run-test in the current directory. If any test fails, report the error and stop."
], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

fail_seen_time = None
proc_end_time = None

for line in iter(proc.stdout.readline, ''):
    elapsed = time.time() - t0
    line_clean = line.strip()
    if line_clean:
        print(f"[{elapsed:6.2f}s] {line_clean}")
    if "FAIL src/auth.test.ts" in line_clean and fail_seen_time is None:
        fail_seen_time = elapsed
    if "Token expired (status 401)" in line_clean and elapsed > 20:
        if proc_end_time is None:
            proc_end_time = elapsed

proc.wait()
total_time = time.time() - t0
print(f"\n--- OpenCode Results ---")
print(f"Total Wall Time: {total_time:.2f}s")
print(f"Failure emitted in stream at: {fail_seen_time}s")
print(f"Final model completion at: {proc_end_time or total_time:.2f}s")
