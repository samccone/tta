import os
import sys
import time
import json
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_TEST_CMD = os.path.join(SCRIPT_DIR, "run-test")
FX_BIN = os.path.join(SCRIPT_DIR, "fx")

env = os.environ.copy()
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k] = v.strip('"').strip("'")

if "AI_GATEWAY_API_KEY" not in env and "VERCEL_TOKEN" in env:
    env["AI_GATEWAY_API_KEY"] = env["VERCEL_TOKEN"]

if "AI_GATEWAY_API_KEY" not in env:
    print("[ERROR] AI_GATEWAY_API_KEY (or VERCEL_TOKEN) is not set in .env or environment.")
    sys.exit(1)

t0 = time.time()
print(f"[{time.strftime('%X')}] Spawning Vercel FX (v0.0.13) with live Vercel AI Gateway (openai/gpt-4o-mini)...")

prompt = f"Run {RUN_TEST_CMD} in the current directory. If any test fails, explain the exact failure and stop."
cmd = [
    FX_BIN, "ask",
    "--yolo",
    "--model", "openai/gpt-4o-mini",
    "--json",
    "--no-save",
    prompt
]

proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

t_fail_seen = None
t_subproc_done = None
t_llm_done = None
raw_output = []

for line in iter(proc.stdout.readline, ""):
    elapsed = time.time() - t0
    line_clean = line.strip()
    if not line_clean:
        continue
    raw_output.append(line_clean)
    print(f"[{elapsed:6.2f}s] {line_clean[:120]}")
    
    if "FAIL src/auth.test.ts" in line_clean and t_fail_seen is None:
        t_fail_seen = elapsed
    if ("Ran all test suites" in line_clean or "Test run failed with exit code 1" in line_clean) and t_subproc_done is None:
        t_subproc_done = elapsed

proc.wait()
t_llm_done = time.time() - t0

# Parse JSON from output
parsed_json = None
for l in reversed(raw_output):
    if l.startswith("{") and l.endswith("}"):
        try:
            parsed_json = json.loads(l)
            break
        except Exception:
            pass

print(f"\n" + "=" * 80)
print(f"VERCEL FX LIVE PRODUCTION RUN COMPLETE")
print(f"=" * 80)
print(f"Total Wall-Clock Time:  {t_llm_done:.2f}s")
print(f"Failure Emitted:        {t_fail_seen:.2f}s" if t_fail_seen else "Failure Emitted: Not detected")
print(f"Subprocess Completed:   {t_subproc_done:.2f}s" if t_subproc_done else "Subprocess Completed: Not detected")
print(f"Model First Awareness:  {t_subproc_done:.2f}s" if t_subproc_done else f"{t_llm_done:.2f}s")
print(f"Wasted Latency:         {(t_subproc_done - t_fail_seen):.2f}s" if (t_subproc_done and t_fail_seen) else "N/A")

if parsed_json:
    usage = parsed_json.get("usage", {})
    tool_calls = parsed_json.get("tool_calls", [])
    print(f"Model:                  {parsed_json.get('model')}")
    print(f"Resolved Provider:      {parsed_json.get('resolved_provider')}")
    print(f"Tokens Consumed:        input={usage.get('input_tokens')}, output={usage.get('output_tokens')}")
    if tool_calls:
        tc = tool_calls[0]
        cmd_res = tc.get("command_result", {})
        print(f"Tool Duration:          {cmd_res.get('duration_ms')}ms")
        print(f"Tool Exit Code:         {cmd_res.get('exit_code')}")
    print(f"Final Output Summary:   {parsed_json.get('final_output', '')[:180]}...")
