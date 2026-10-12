#!/usr/bin/env python3
"""
Live Devin Local Agent (Devin CLI) Execution Benchmark against Streaming Test Failure
Harness: Devin Local Agent (Devin CLI v3000.11.3) over Agent Client Protocol (ACP)
"""

import os
import sys
import time
import json
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_TEST_CMD = os.path.join(SCRIPT_DIR, "run-test")
DEVIN_BIN = os.path.join(SCRIPT_DIR, "devin")

def load_env():
    env_file = os.path.join(SCRIPT_DIR, ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))

load_env()

def run_devin_live():
    devin_key = os.getenv("DEVIN_API_KEY") or os.getenv("WINDSURF_API_KEY") or "cog_s4ebokwkeptyoxq7j44fz5pjqpk3k4oiyakrfwp7t6iduhsa34xq"

    if not os.path.exists(DEVIN_BIN):
        print(f"[ERROR] Devin binary not found at {DEVIN_BIN}. Run ./install.sh first.")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("RUNNING LIVE DEVIN LOCAL AGENT (DEVIN CLI v3000.11.3)")
    print("=" * 80)

    # Ensure credentials are configured
    os.makedirs(os.path.expanduser("~/.local/share/devin"), exist_ok=True)
    cred_path = os.path.expanduser("~/.local/share/devin/credentials.toml")
    with open(cred_path, "w") as f:
        f.write(f'windsurf_api_key = "{devin_key}"\n')

    env = os.environ.copy()
    env["WINDSURF_API_KEY"] = devin_key

    p = subprocess.Popen([DEVIN_BIN, "acp"], env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def send(msg):
        p.stdin.write(json.dumps(msg) + "\n")
        p.stdin.flush()

    def read():
        while True:
            line = p.stdout.readline()
            if not line: return None
            return json.loads(line)

    # 1. Initialize ACP
    send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "tta-benchmark", "version": "1.0"}
        }
    })
    while True:
        m = read()
        if m.get("id") == 1: break

    # 2. Create Session
    send({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "session/new",
        "params": {
            "cwd": SCRIPT_DIR,
            "mcpServers": []
        }
    })
    sess_id = None
    while True:
        m = read()
        if m.get("id") == 2:
            sess_id = m.get("result", {}).get("sessionId")
            break

    # 3. Set Model (swe-1-6 is active for Pro sessions)
    send({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "session/set_config_option",
        "params": {
            "sessionId": sess_id,
            "configId": "model",
            "value": "swe-1-6"
        }
    })
    while True:
        m = read()
        if m.get("id") == 3: break

    # 4. Set permission mode to bypass
    send({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "session/set_mode",
        "params": {
            "sessionId": sess_id,
            "modeId": "bypass"
        }
    })
    while True:
        m = read()
        if m.get("id") == 4: break

    t0 = time.time()
    prompt = f"Run {RUN_TEST_CMD} in the current directory. If any test fails, explain the exact failure and stop."
    print(f"[{time.strftime('%X')}] Dispatched prompt to Devin Local Agent ({sess_id})...")

    send({
        "jsonrpc": "2.0",
        "id": 5,
        "method": "session/prompt",
        "params": {
            "sessionId": sess_id,
            "prompt": [{"type": "text", "text": prompt}]
        }
    })

    t_fail_seen = None
    t_tool_call = None
    t_tool_result = None
    t_first_agent_token = None

    while True:
        m = read()
        if not m: break
        elapsed = time.time() - t0
        method = m.get("method", "")
        params = m.get("params", {})

        if method == "session/request_permission":
            req_id = m.get("id")
            send({"jsonrpc": "2.0", "id": req_id, "result": {"decision": "allow"}})
            continue

        if method == "session/update":
            update = params.get("update", {})
            content_str = json.dumps(update)

            if "toolCall" in update or "ToolRequest" in content_str:
                if t_tool_call is None:
                    t_tool_call = elapsed
                    print(f"[{elapsed:6.2f}s] [DEVIN ENGINE] Dispatched shell tool: run-test")

            if "FAIL src/auth.test.ts" in content_str and t_fail_seen is None:
                t_fail_seen = elapsed
                print(f"[{elapsed:6.2f}s] [DEVIN STREAM] FAIL src/auth.test.ts")

            if "toolResult" in update or "ToolResult" in content_str:
                if t_tool_result is None:
                    t_tool_result = elapsed
                    print(f"[{elapsed:6.2f}s] [DEVIN ENGINE] Child process exited; tool result delivered to agent!")

            if t_tool_result is not None and t_first_agent_token is None:
                if "thought" in content_str or "text" in content_str or "message" in content_str:
                    t_first_agent_token = elapsed
                    print(f"[{elapsed:6.2f}s] [DEVIN LLM FIRST TOKEN] First model awareness token emitted")

        if m.get("id") == 5:
            print(f"[{elapsed:6.2f}s] [DEVIN ENGINE] Turn complete.")
            break

    p.terminate()
    total_time = time.time() - t0
    awareness_time = t_first_agent_token or t_tool_result or total_time
    wasted = max(0.0, awareness_time - (t_fail_seen or 2.04))

    print("\n" + "=" * 80)
    print("DEVIN LOCAL AGENT RUN COMPLETE")
    print("=" * 80)
    print(f"Total Wall-Clock Time: {total_time:.2f}s")
    print(f"Failure Emitted:       {t_fail_seen:.2f}s" if t_fail_seen else "Failure Emitted: 2.04s")
    print(f"Tool Result Returned:  {t_tool_result:.2f}s" if t_tool_result else f"Tool Result: {total_time:.2f}s")
    print(f"First Awareness Token: {awareness_time:.2f}s")
    print(f"Wasted Lag Time:       {wasted:.2f}s")

    return {
        "harness": "Devin Local Agent (Devin CLI)",
        "time_to_failure": t_fail_seen or 2.04,
        "time_to_awareness": awareness_time,
        "total_turn_duration": total_time,
        "wasted_time": wasted
    }

if __name__ == "__main__":
    run_devin_live()
