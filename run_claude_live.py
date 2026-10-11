#!/usr/bin/env python3
"""
Live Anthropic Claude Code CLI Execution against Real Production Anthropic API
Uses live tokens on model claude-sonnet-5-5.
"""

import os
import sys
import time
import json
import socket
import threading
import subprocess
import urllib.request
import http.server

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_TEST_CMD = os.path.join(SCRIPT_DIR, "run-test")
CLAUDE_BIN = os.path.join(SCRIPT_DIR, "node_modules/@anthropic-ai/claude-code-darwin-arm64/claude")

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

ANT_KEY = os.getenv("ANTHROPIC_API_KEY")
ANT_WS = os.getenv("ANTHROPIC_WORKSPACE_ID")
TARGET_URL = "https://api.anthropic.com"

if not ANT_KEY:
    print("[ERROR] ANTHROPIC_API_KEY is not set in .env or environment.")
    sys.exit(1)

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def main():
    port = get_free_port()
    t0 = time.time()

    class ProxyHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

        def do_POST(self):
            length = int(self.headers.get('content-length', 0))
            body = self.rfile.read(length)
            
            req_headers = {}
            for k, v in self.headers.items():
                if k.lower() not in ('host', 'content-length', 'connection'):
                    req_headers[k] = v
            if ANT_WS:
                req_headers['anthropic-workspace-id'] = ANT_WS
            
            # Forward directly to Anthropic
            req = urllib.request.Request(
                TARGET_URL + self.path,
                data=body,
                headers=req_headers,
                method='POST'
            )
            try:
                with urllib.request.urlopen(req) as resp:
                    self.send_response(resp.status)
                    for h, val in resp.headers.items():
                        if h.lower() not in ('content-length', 'transfer-encoding', 'connection'):
                            self.send_header(h, val)
                    res_body = resp.read()
                    self.send_header('Content-Length', str(len(res_body)))
                    self.end_headers()
                    self.wfile.write(res_body)
            except urllib.error.HTTPError as e:
                err_body = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_body)

    server = http.server.HTTPServer(('127.0.0.1', port), ProxyHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    env = os.environ.copy()
    env['ANTHROPIC_BASE_URL'] = f'http://127.0.0.1:{port}'
    env['ANTHROPIC_API_KEY'] = ANT_KEY
    env['CLAUDE_CODE_SIMPLE'] = '1'

    print(f"[{time.strftime('%X')}] Spawning Anthropic Claude Code CLI with LIVE Anthropic API...")
    prompt = f"Run {RUN_TEST_CMD} in the current directory. If any test fails, explain the exact failure and stop."
    
    proc = subprocess.Popen([
        CLAUDE_BIN,
        '-p',
        '--dangerously-skip-permissions',
        '--model', 'claude-haiku-4-5-20251001',
        prompt
    ], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    for line in iter(proc.stdout.readline, ''):
        elapsed = time.time() - t0
        line_clean = line.strip()
        if line_clean:
            print(f"[{elapsed:6.2f}s] {line_clean}")

    proc.stdout.close()
    proc.wait()
    total_time = time.time() - t0
    print(f"\n[{total_time:6.2f}s] REAL ANTHROPIC CLAUDE CODE LIVE RUN COMPLETE. Total wall-clock duration: {total_time:.2f}s")

if __name__ == "__main__":
    main()
