import os
import sys
import time
from smolagents import ToolCallingAgent, Tool, OpenAIServerModel

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

import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_TEST_CMD = os.path.join(SCRIPT_DIR, "run-test")

class BashTool(Tool):
    name = "bash"
    description = "Executes a shell command and returns output."
    inputs = {
        "command": {"type": "string", "description": "Command to run"}
    }
    output_type = "string"

    def forward(self, command: str) -> str:
        t_start = time.time()
        print(f"[{time.strftime('%X')}] [SMOLAGENTS BASH TOOL] Executing: {command}")
        res = subprocess.run(command, shell=True, capture_output=True, text=True)
        t_end = time.time()
        print(f"[{time.strftime('%X')}] [SMOLAGENTS BASH TOOL] Subprocess completed in {t_end - t_start:.2f}s with exit code {res.returncode}")
        return res.stdout + res.stderr

t0 = time.time()
model = OpenAIServerModel(
    model_id="gpt-4o-mini",
    api_key=os.environ.get("OPENAI_API_KEY")
)
agent = ToolCallingAgent(tools=[BashTool()], model=model)

print(f"[{time.strftime('%X')}] Running Smolagents with gpt-4o-mini...")
result = agent.run(f"Run {RUN_TEST_CMD} in the current directory and explain what failed.")
t_total = time.time() - t0
print(f"\n--- Smolagents Results ---")
print(f"Total Wall Time: {t_total:.2f}s")
print(f"Agent Final Answer: {str(result)[:150]}...")
