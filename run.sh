#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

MODE="auto"            # auto|prepare
FORCE_REINSTALL="false"
FORCE_REINDEX="false"
FORCE_LLM_CHECK="false"
NO_START="false"

for arg in "$@"; do
  case "$arg" in
    --prepare-only) MODE="prepare" ;;
    --reinstall) FORCE_REINSTALL="true" ;;
    --reindex) FORCE_REINDEX="true" ;;
    --check) FORCE_LLM_CHECK="true" ;;
    --no-start) NO_START="true" ;;
    --help|-h)
      echo "用法: ./run.sh [--prepare-only] [--reinstall] [--reindex] [--check] [--no-start]"
      echo "  --prepare-only  只准备环境与依赖，不构建索引、不启动应用"
      echo "  --reinstall     强制重装 requirements.txt"
      echo "  --reindex       强制重建索引"
      echo "  --check         强制执行一次 LLM API 检查"
      echo "  --no-start      完成后不启动 Streamlit"
      exit 0
      ;;
    *)
      echo "❌ 未知参数: $arg"
      exit 1
      ;;
  esac
done

echo "🚀 一键启动：项目级环境自修复 + 索引按需重建 + 应用启动"

if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="python3.11"
else
  echo "❌ 未找到 python3.11，请先安装 Python 3.11"
  echo "macOS: brew install python@3.11"
  exit 1
fi

REBUILD_VENV="false"
if [ ! -d "venv" ]; then
  REBUILD_VENV="true"
else
  VENV_PY_VER="$(./venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "unknown")"
  if [ "$VENV_PY_VER" != "3.11" ]; then
    REBUILD_VENV="true"
  fi
fi

if [ "$REBUILD_VENV" = "true" ]; then
  echo "📦 使用 Python 3.11 重建虚拟环境"
  rm -rf venv
  "$PYTHON_BIN" -m venv venv
fi

source venv/bin/activate

if [ ! -f "requirements.txt" ]; then
  echo "❌ 缺少 requirements.txt"
  exit 1
fi

REQ_HASH="$(shasum -a 256 requirements.txt | awk '{print $1}')"
STAMP_FILE="venv/.requirements.sha256"
OLD_HASH=""
if [ -f "$STAMP_FILE" ]; then
  OLD_HASH="$(cat "$STAMP_FILE")"
fi

NEED_INSTALL="false"
if [ "$FORCE_REINSTALL" = "true" ] || [ "$REQ_HASH" != "$OLD_HASH" ]; then
  NEED_INSTALL="true"
fi

if [ "$NEED_INSTALL" = "true" ]; then
  echo "📥 安装/更新依赖"
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
  echo "$REQ_HASH" > "$STAMP_FILE"
else
  echo "✅ 依赖无变化，跳过安装"
fi

if [ ! -f ".env" ]; then
  echo "❌ 未找到 .env，请先在项目根目录创建"
  echo "OPENAI_API_KEY=sk-..."
  echo "OPENAI_BASE_URL=https://api.deepseek.com/v1"
  echo "OPENAI_MODEL=deepseek-chat"
  echo "OPENAI_EMBED_MODEL=local:BAAI/bge-small-zh-v1.5"
  exit 1
fi

if [ "$MODE" = "prepare" ]; then
  echo "✅ 环境准备完成（prepare-only）"
  exit 0
fi

LLM_CHECK_STAMP="venv/.llm_check.ok"
NEED_LLM_CHECK="false"
if [ "$FORCE_LLM_CHECK" = "true" ] || [ ! -f "$LLM_CHECK_STAMP" ]; then
  NEED_LLM_CHECK="true"
fi

if [ "$NEED_LLM_CHECK" = "true" ]; then
  echo "🔍 首次/强制检查 LLM API"
  python tools/check_llm_api.py
  date > "$LLM_CHECK_STAMP"
else
  echo "✅ LLM API 已检查过，默认跳过（如需重查用 --check）"
fi

INDEX_DIR="outputs/rag_index"
INDEX_STAMP="$INDEX_DIR/.index_fingerprint"

CURRENT_FINGERPRINT="$(python - <<'PY'
import hashlib
from pathlib import Path

root = Path('.')
items = []

# 文档库
for p in sorted((root / 'data').rglob('*')) if (root / 'data').exists() else []:
    if p.is_file():
        s = p.stat()
        items.append((str(p.relative_to(root)), s.st_size, s.st_mtime_ns))

# 本地数据库（若存在）
db = root / 'company.db'
if db.exists() and db.is_file():
    s = db.stat()
    items.append((str(db.relative_to(root)), s.st_size, s.st_mtime_ns))

# 索引构建脚本（变更也应触发重建）
build = root / 'src' / 'rag' / 'build_index.py'
if build.exists() and build.is_file():
    s = build.stat()
    items.append((str(build.relative_to(root)), s.st_size, s.st_mtime_ns))

h = hashlib.sha256()
for rel, size, mtime in items:
    h.update(rel.encode('utf-8'))
    h.update(str(size).encode('utf-8'))
    h.update(str(mtime).encode('utf-8'))

print(h.hexdigest())
PY
)"

NEED_REINDEX="false"
if [ "$FORCE_REINDEX" = "true" ]; then
  NEED_REINDEX="true"
elif [ ! -d "$INDEX_DIR" ] || [ ! -f "$INDEX_DIR/index_store.json" ]; then
  NEED_REINDEX="true"
elif [ ! -f "$INDEX_STAMP" ]; then
  NEED_REINDEX="true"
else
  LAST_FINGERPRINT="$(cat "$INDEX_STAMP")"
  if [ "$CURRENT_FINGERPRINT" != "$LAST_FINGERPRINT" ]; then
    NEED_REINDEX="true"
  fi
fi

if [ "$NEED_REINDEX" = "true" ]; then
  echo "📚 检测到知识源变更，重建索引"
  python src/rag/build_index.py
  mkdir -p "$INDEX_DIR"
  echo "$CURRENT_FINGERPRINT" > "$INDEX_STAMP"
else
  echo "✅ 未检测到知识源变更，跳过索引重建"
fi

if [ "$NO_START" = "true" ]; then
  echo "✅ 执行完成（no-start）"
  exit 0
fi

echo "🌐 启动 Streamlit"
python -m streamlit run src/app/streamlit_app.py
