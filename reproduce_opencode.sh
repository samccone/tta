#!/usr/bin/env bash
# reproduce_opencode.sh: Demonstrate OpenCode execution model on streaming CLI commands

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCODE_BIN="$SCRIPT_DIR/opencode"
TEST_SCRIPT="$SCRIPT_DIR/run-test"

echo "======================================================================"
echo " Anomaly OpenCode Streaming Execution Reproduction"
echo "======================================================================"
echo "Binary:         $OPENCODE_BIN (v1.18.35)"
echo "Target Command: $TEST_SCRIPT"
echo "Code References:"
echo "  - anomaly-opencode/packages/core/src/tool/plugin/shell.ts (shell tool, jobs.block)"
echo "  - anomaly-opencode/packages/core/src/job.ts (jobs.block -> Deferred.await(job.done))"
echo "  - anomaly-opencode/packages/core/src/shell.ts (handle.exitCode, sh_<id>.out file)"
echo "  - anomaly-opencode/packages/core/src/session/runner/step.ts (Fiber.awaitAll step barrier)"
echo "======================================================================"
echo ""
echo "Key architectural mechanism in OpenCode:"
echo "1. The foreground shell tool runs:"
echo "     const result = yield* jobs.block({ id: job.id, sessionID: context.sessionID })"
echo "     ... return yield* Deferred.await(settled)"
echo "2. jobs.block() races job.done against job.backgrounded, blocking the Effect fiber."
echo "3. While subprocess output is written to disk (sh_<id>.out) and rendered to the"
echo "   human TUI/Web UI via 1Hz polling, the LLM agent is completely blocked until"
echo "   the entire process terminates at t = 22.2s."
echo ""
echo "Running OpenCode execution simulation benchmark..."
python3 -u "$SCRIPT_DIR/run_benchmark.py" --mode opencode
