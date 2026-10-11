#!/usr/bin/env python3
"""
Convenience entrypoint for running the empirical unmocked harness benchmarks.
Delegates to run_real_harnesses.py
"""
import sys
import subprocess
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REAL_BENCHMARK = os.path.join(SCRIPT_DIR, "run_real_harnesses.py")

if __name__ == "__main__":
    cmd = [sys.executable, REAL_BENCHMARK] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))
