#!/usr/bin/env bash
set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  AI Coding Harness Benchmark Setup                             ${NC}"
echo -e "${BLUE}================================================================${NC}"

# 1. Check Python
echo -e "\n${YELLOW}[1/4] Checking Python environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is required but not installed.${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${GREEN}✓ Found ${PYTHON_VERSION}${NC}"

# Install Python requirements
echo -e "Installing Python dependencies (requirements.txt)..."
python3 -m pip install -q -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# 2. Check Node / npm
echo -e "\n${YELLOW}[2/4] Checking Node.js & npm environment...${NC}"
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Warning: npm is not found in PATH. Claude Code and Codex CLI require npm.${NC}"
else
    NODE_VERSION=$(node --version 2>&1 || echo "node")
    NPM_VERSION=$(npm --version 2>&1 || echo "npm")
    echo -e "${GREEN}✓ Found Node ${NODE_VERSION} / npm ${NPM_VERSION}${NC}"
    echo -e "Installing npm packages (@anthropic-ai/claude-code, @openai/codex)..."
    npm install --silent
    echo -e "${GREEN}✓ Node packages installed${NC}"
fi

# 3. Unpack and verify standalone harness binaries
echo -e "\n${YELLOW}[3/4] Checking standalone harness binaries...${NC}"

# OpenCode binary
if [ ! -f "${SCRIPT_DIR}/opencode" ] && [ -f "${SCRIPT_DIR}/opencode.zip" ]; then
    echo -e "Extracting opencode from opencode.zip..."
    unzip -q -o "${SCRIPT_DIR}/opencode.zip" -d "${SCRIPT_DIR}"
fi

# Plandex binary
if [ ! -f "${SCRIPT_DIR}/plandex" ] && [ -f "${SCRIPT_DIR}/plandex.tar.gz" ]; then
    echo -e "Extracting plandex from plandex.tar.gz..."
    tar -xzf "${SCRIPT_DIR}/plandex.tar.gz" -C "${SCRIPT_DIR}"
fi

# Goose binary
if [ ! -f "${SCRIPT_DIR}/goose" ] && [ -f "${SCRIPT_DIR}/goose.tar.gz" ]; then
    echo -e "Extracting goose from goose.tar.gz..."
    tar -xzf "${SCRIPT_DIR}/goose.tar.gz" -C "${SCRIPT_DIR}"
fi

# Devin Local Agent binary
if [ ! -f "${SCRIPT_DIR}/devin" ]; then
    echo -e "Downloading Devin CLI binary..."
    if [ ! -f "${SCRIPT_DIR}/devin.tar.gz" ]; then
        curl -fsSL "https://static.devin.ai/cli/3000.11.3/devin-3000.11.3-aarch64-apple-darwin.tar.gz" -o "${SCRIPT_DIR}/devin.tar.gz" || true
    fi
    if [ -f "${SCRIPT_DIR}/devin.tar.gz" ]; then
        tar -xzf "${SCRIPT_DIR}/devin.tar.gz" bin/devin 2>/dev/null || tar -xzf "${SCRIPT_DIR}/devin.tar.gz" devin 2>/dev/null || true
        [ -f "${SCRIPT_DIR}/bin/devin" ] && mv "${SCRIPT_DIR}/bin/devin" "${SCRIPT_DIR}/devin" && rmdir "${SCRIPT_DIR}/bin" 2>/dev/null || true
    fi
fi

# Ensure executable permissions
chmod +x "${SCRIPT_DIR}/run-test" 2>/dev/null || true
[ -f "${SCRIPT_DIR}/fx" ] && chmod +x "${SCRIPT_DIR}/fx"
[ -f "${SCRIPT_DIR}/opencode" ] && chmod +x "${SCRIPT_DIR}/opencode"
[ -f "${SCRIPT_DIR}/plandex" ] && chmod +x "${SCRIPT_DIR}/plandex"
[ -f "${SCRIPT_DIR}/goose" ] && chmod +x "${SCRIPT_DIR}/goose"
[ -f "${SCRIPT_DIR}/devin" ] && chmod +x "${SCRIPT_DIR}/devin"

echo -e "${GREEN}✓ Standalone binaries verified:${NC}"
[ -f "${SCRIPT_DIR}/fx" ] && echo -e "  - Vercel FX: $(${SCRIPT_DIR}/fx --version 2>/dev/null || echo 'installed')"
[ -f "${SCRIPT_DIR}/opencode" ] && echo -e "  - OpenCode:  $(${SCRIPT_DIR}/opencode --version 2>/dev/null || echo 'installed')"
[ -f "${SCRIPT_DIR}/devin" ] && echo -e "  - Devin:     $(${SCRIPT_DIR}/devin --version 2>/dev/null || echo 'installed')"

# 4. Check Environment (.env)
echo -e "\n${YELLOW}[4/4] Checking API Keys and environment...${NC}"
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    if [ -f "${SCRIPT_DIR}/.env.example" ]; then
        cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"
        echo -e "${YELLOW}Created .env from .env.example${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

echo -e "\n${BLUE}================================================================${NC}"
echo -e "${GREEN}Setup complete!${NC}"
echo -e "You can now run the benchmark using:"
echo -e "  ${YELLOW}./run_benchmark.py${NC}            # Run all harnesses (unmocked mock-LLM protocol)"
echo -e "  ${YELLOW}./run_benchmark.py --harness human${NC} # Run human baseline"
echo -e "  ${YELLOW}./run_live_tokens.py${NC}          # Run with live frontier APIs (requires .env keys)"
echo -e "${BLUE}================================================================${NC}"
