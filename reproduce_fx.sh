#!/usr/bin/env bash
# reproduce_fx.sh: Demonstrate Vercel FX execution model on streaming CLI commands

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FX_BIN="$SCRIPT_DIR/fx"
TEST_SCRIPT="$SCRIPT_DIR/run-test"

echo "======================================================================"
echo " Vercel FX Streaming Execution Reproduction"
echo "======================================================================"
echo "Binary:         $FX_BIN (v0.0.13)"
echo "Target Command: $TEST_SCRIPT"
echo "Code References:"
echo "  - vercel-fx/src/builtins/tools.zig (shell_description, default yield_time_ms = 30000)"
echo "  - vercel-fx/src/tools/shell/shell.zig (callRun, finishPrepared)"
echo "  - vercel-fx/src/core/execution/managed_execution.zig (startCaptured blocking loop)"
echo "  - vercel-fx/src/core/execution/command_runner.zig (OutputChunkEmitter streaming)"
echo "======================================================================"
echo ""
echo "Key architectural mechanism in Vercel FX:"
echo "1. Default yield_time_ms is 30000 ms (30 seconds)."
echo "2. managed_execution.zig:startCaptured() executes:"
echo "     while (true) {"
echo "         if (entry.isTerminal()) break;"
echo "         if (elapsed >= input.yield_time_ms) break;"
echo "         io_mod.sleep(10ms);"
echo "     }"
echo "3. While chunks stream live to the user's terminal UI via onCommandOutputChunk,"
echo "   the agent dispatch thread is blocked sleeping in 10ms intervals until the"
echo "   subprocess terminates at t = 22.18s."
echo ""
echo "Running Vercel FX execution simulation benchmark..."
python3 -u "$SCRIPT_DIR/run_benchmark.py" --mode fx
