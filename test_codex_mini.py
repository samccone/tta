import os
import sys
import time
import json
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_TEST_CMD = os.path.join(SCRIPT_DIR, "run-test")
CODEX_BIN = os.path.join(SCRIPT_DIR, "node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex")

env = os.environ.copy()
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k] = v.strip('"').strip("'")

# Ensure no mock overrides
env.pop("OPENAI_BASE_URL", None)

if "OPENAI_API_KEY" not in env:
    print("[ERROR] OPENAI_API_KEY is not set in .env or environment.")
    sys.exit(1)

t0 = time.time()
print(f"[{time.strftime('%X')}] Spawning OpenAI Codex CLI with gpt-4o-mini...")

prompt = f"Run {RUN_TEST_CMD} in this directory. If any test fails, explain the exact failure and stop."
cmd = [
    CODEX_BIN, "exec",
    "--skip-git-repo-check",
    "--dangerously-bypass-approvals-and-sandbox",
    "-m", "gpt-4o-mini",
    "--json",
    prompt
]

proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

t_fail_seen = None
t_first_agent_token = None
t_pty_yield = None

for line in iter(proc.stdout.readline, ""):
    elapsed = time.time() - t0
    line_clean = line.strip()
    if not line_clean:
        continue
    try:
        ev = json.loads(line_clean)
        ev_type = ev.get("type", "")
        item = ev.get("item", {})
        item_type = item.get("type", "")
        
        if ev_type == "item.completed" and item_type == "command_execution":
            t_pty_yield = elapsed
            print(f"[{elapsed:6.2f}s] [CODEX PTY YIELD] Command completed in PTY: {item.get('command', '')} exit_code={item.get('exit_code')}")
        elif ev_type == "item.completed" and item_type == "agent_message":
            if t_first_agent_token is None:
                t_first_agent_token = elapsed
            print(f"[{elapsed:6.2f}s] [CODEX AGENT MESSAGE] {item.get('text', '')[:120]}...")
        elif ev_type == "turn.completed":
            print(f"[{elapsed:6.2f}s] [CODEX TURN COMPLETED] usage={ev.get('usage')}")
        else:
            if elapsed < 15 or "fail" in line_clean.lower():
                print(f"[{elapsed:6.2f}s] [CODEX EVENT] {ev_type} {item_type}")
    except json.JSONDecodeError:
        print(f"[{elapsed:6.2f}s] [RAW] {line_clean[:120]}")

proc.stdout.close()
proc.wait()
total_time = time.time() - t0
print(f"\n--- OpenAI Codex (gpt-4o-mini) Results ---")
print(f"Total Wall Time: {total_time:.2f}s")
print(f"PTY Yield Window: {t_pty_yield:.2f}s" if t_pty_yield else "PTY Yield: None")
print(f"First Agent Message: {t_first_agent_token:.2f}s" if t_first_agent_token else "First Agent Message: None")
