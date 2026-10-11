import os
import sys
import time
import subprocess

if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k] = v.strip('"').strip("'")

if not os.environ.get("OPENAI_API_KEY"):
    print("[ERROR] OPENAI_API_KEY is not set in .env or environment.")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_TEST_CMD = os.path.join(SCRIPT_DIR, "run-test")

t0 = time.time()
print(f"[{time.strftime('%X')}] Running Aider CLI with gpt-4o-mini...")

proc = subprocess.Popen([
    "python3", "-m", "aider",
    "--no-git",
    "--model", "openai/gpt-4o-mini",
    "--test-cmd", RUN_TEST_CMD,
    "--test",
    "--no-analytics",
    "--exit"
], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

fail_seen_time = None
first_llm_time = None

for line in iter(proc.stdout.readline, ''):
    elapsed = time.time() - t0
    line_clean = line.strip()
    if line_clean:
        print(f"[{elapsed:6.2f}s] {line_clean}")
    if "FAIL src/auth.test.ts" in line_clean and fail_seen_time is None:
        fail_seen_time = elapsed
    if ("Test failed" in line_clean or "Fixing" in line_clean) and elapsed > 20:
        if first_llm_time is None:
            first_llm_time = elapsed

proc.wait()
total_time = time.time() - t0
print(f"\n--- Aider Results ---")
print(f"Total Wall Time: {total_time:.2f}s")
print(f"Failure in stream at: {fail_seen_time}s")
print(f"Aider reaction at: {first_llm_time or total_time:.2f}s")
