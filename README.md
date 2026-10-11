# AI Coding Harness Streaming Benchmark

For the full writeup and analysis, see: https://samsaccone.com/posts/harness-lag.html

## Installation

Run the setup script:

```bash
./install.sh
```

## Running the Benchmarks

### 1. Mock LLM Benchmark (Zero API Latency Overhead)

Run all harnesses:

```bash
./run_benchmark.py
```

Run an individual harness:

```bash
./run_benchmark.py --harness human
./run_benchmark.py --harness codex
./run_benchmark.py --harness claude
./run_benchmark.py --harness fx
./run_benchmark.py --harness opencode
./run_benchmark.py --harness aider
./run_benchmark.py --harness smolagents
```

### 2. Live API Token Benchmark (Real Frontier APIs)

1. Set your API keys in `.env` (copy from `.env.example`):

```bash
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
```

2. Run the live benchmarks:

```bash
python3 run_live_tokens.py
```

Or run individual live harness scripts:

```bash
python3 test_codex_mini.py
python3 run_claude_live.py
python3 test_fx_live.py
python3 test_opencode_live.py
python3 test_aider_mini.py
python3 test_smolagents_mini.py
```
