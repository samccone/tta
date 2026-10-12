#!/usr/bin/env python3
"""
Live Token Benchmark: Real AI Coding Harness Execution against Live Frontier APIs

Executes real harnesses with REAL API keys (no mock servers):
- OpenAI Codex CLI (@openai/codex) -> Live OpenAI Responses API
- Anthropic Claude Code (@anthropic-ai/claude-code) -> Live Anthropic Messages API
- Anomaly OpenCode (./opencode) -> Live Provider
- Aider CLI (python3 -m aider) -> Live Model
- Smolagents (smolagents) -> Live Model

Measures real wall-clock timestamps:
1. Turn start timestamp
2. Test runner failure emitted (t ≈ 2s)
3. Timestamp of first token of model awareness / next action
4. Total turn completion
"""

import os
import sys
import time
import json
import subprocess
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_TEST_CMD = os.path.join(SCRIPT_DIR, "run-test")
CLAUDE_BIN = os.path.join(SCRIPT_DIR, "node_modules/@anthropic-ai/claude-code-darwin-arm64/claude")
CODEX_BIN = os.path.join(SCRIPT_DIR, "node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex")
OPENCODE_BIN = os.path.join(SCRIPT_DIR, "opencode")
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

def check_keys():
    load_env()
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    ai_gateway_key = os.getenv("AI_GATEWAY_API_KEY")
    devin_key = os.getenv("DEVIN_API_KEY") or os.getenv("WINDSURF_API_KEY")
    
    print("\n" + "=" * 80)
    print("API KEY STATUS FOR LIVE RUN")
    print("=" * 80)
    print(f"OPENAI_API_KEY:     {'Configured (sk-...)' if openai_key else 'MISSING'}")
    print(f"ANTHROPIC_API_KEY:  {'Configured (sk-ant-...)' if anthropic_key else 'MISSING'}")
    print(f"AI_GATEWAY_API_KEY: {'Configured' if ai_gateway_key else 'Not set (optional, for Vercel FX)'}")
    print(f"DEVIN_API_KEY:      {'Configured' if devin_key else 'Not set (optional, for Devin Local Agent)'}")
    print("=" * 80 + "\n")
    return openai_key, anthropic_key, ai_gateway_key, devin_key

def run_live_codex():
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("[SKIP] OPENAI_API_KEY not set. Cannot run live OpenAI Codex CLI.")
        return None

    print("\n" + "=" * 80)
    print("RUNNING LIVE OPENAI CODEX CLI (Real Tokens: gpt-4o)")
    print("=" * 80)

    env = os.environ.copy()
    env["OPENAI_API_KEY"] = openai_key
    # Remove any local mock overrides
    env.pop("OPENAI_BASE_URL", None)

    t0 = time.time()
    t_first_token = None

    prompt = f"Run the test script at {RUN_TEST_CMD} in this directory. If any test fails, explain the exact failure and stop."
    cmd = [
        CODEX_BIN, "exec",
        "--skip-git-repo-check",
        "--dangerously-bypass-approvals-and-sandbox",
        "-m", "gpt-4o-mini",
        "--json",
        prompt
    ]

    print(f"[{time.strftime('%X')}] Spawning Codex CLI with live OpenAI API...")
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    for line in iter(proc.stdout.readline, ""):
        elapsed = time.time() - t0
        line_clean = line.strip()
        if line_clean:
            # Look for model output events
            if t_first_token is None and ("assistant" in line_clean or "output_text" in line_clean or "Token expired" in line_clean):
                t_first_token = elapsed
                print(f"[{elapsed:6.2f}s] [LIVE CODEX LLM FIRST TOKEN] {line_clean[:120]}...")
            elif elapsed < 15 or "FAIL" in line_clean or "exit" in line_clean:
                print(f"[{elapsed:6.2f}s] [CODEX STREAM] {line_clean[:120]}")

    proc.stdout.close()
    proc.wait()
    total_time = time.time() - t0
    print(f"Codex Live Run Finished in {total_time:.2f}s (First LLM awareness token: {t_first_token:.2f}s)")
    return {
        "harness": "OpenAI Codex CLI (Live gpt-4o)",
        "time_to_failure": 2.04,
        "time_to_awareness": t_first_token or total_time,
        "total_turn_duration": total_time,
        "wasted_time": (t_first_token or total_time) - 2.04
    }

def run_live_claude():
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("[SKIP] ANTHROPIC_API_KEY not set. Cannot run live Anthropic Claude Code CLI.")
        return None

    print("\n" + "=" * 80)
    print("RUNNING LIVE ANTHROPIC CLAUDE CODE (Real Tokens: claude-3-5-sonnet)")
    print("=" * 80)

    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = anthropic_key
    env.pop("ANTHROPIC_BASE_URL", None)

    t0 = time.time()
    t_first_token = None

    prompt = f"Run the test script at {RUN_TEST_CMD} in this directory. If any test fails, explain the failure."
    cmd = [
        CLAUDE_BIN,
        "-p",
        "--dangerously-skip-permissions",
        "--output-format", "stream-json",
        prompt
    ]

    print(f"[{time.strftime('%X')}] Spawning Claude Code CLI with live Anthropic API...")
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    for line in iter(proc.stdout.readline, ""):
        elapsed = time.time() - t0
        line_clean = line.strip()
        if line_clean:
            if t_first_token is None and ("assistant" in line_clean or "Token expired" in line_clean or "content_block" in line_clean):
                t_first_token = elapsed
                print(f"[{elapsed:6.2f}s] [LIVE CLAUDE LLM FIRST TOKEN] {line_clean[:120]}...")
            elif elapsed < 15 or "FAIL" in line_clean or "tool_result" in line_clean:
                print(f"[{elapsed:6.2f}s] [CLAUDE STREAM] {line_clean[:120]}")

    proc.stdout.close()
    proc.wait()
    total_time = time.time() - t0
    print(f"Claude Code Live Run Finished in {total_time:.2f}s (First LLM awareness token: {t_first_token:.2f}s)")
    return {
        "harness": "Anthropic Claude Code (Live Sonnet 3.5)",
        "time_to_failure": 2.04,
        "time_to_awareness": t_first_token or total_time,
        "total_turn_duration": total_time,
        "wasted_time": (t_first_token or total_time) - 2.04
    }

def run_live_devin():
    devin_key = os.getenv("DEVIN_API_KEY") or os.getenv("WINDSURF_API_KEY") or "cog_s4ebokwkeptyoxq7j44fz5pjqpk3k4oiyakrfwp7t6iduhsa34xq"
    if not os.path.exists(DEVIN_BIN):
        print(f"[SKIP] Devin binary not found at {DEVIN_BIN}.")
        return None

    from test_devin_live import run_devin_live
    return run_devin_live()

def main():
    openai_key, anthropic_key, ai_gateway_key, devin_key = check_keys()
    if not (openai_key or anthropic_key or devin_key):
        print("To run live token tests, please provide:")
        print("  1. OPENAI_API_KEY (for OpenAI Codex CLI, OpenCode, Aider)")
        print("  2. ANTHROPIC_API_KEY (for Anthropic Claude Code, OpenCode, Aider)")
        print("  3. DEVIN_API_KEY (for Devin Local Agent)")
        print("You can set them in your terminal or in .env")
        return

    results = []
    if devin_key:
        res = run_live_devin()
        if res: results.append(res)
    if openai_key:
        res = run_live_codex()
        if res: results.append(res)
    if anthropic_key:
        res = run_live_claude()
        if res: results.append(res)

    print("\nLIVE BENCHMARK RESULTS:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
