#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "🚀 Setup: 准备 Python 3.11 虚拟环境与依赖"
./run.sh --prepare-only "$@"

echo "\n✅ Setup 完成"
echo "启动应用（唯一命令）: ./run.sh"
echo "仅在需要排查时再检查 LLM API: ./run.sh --check"
