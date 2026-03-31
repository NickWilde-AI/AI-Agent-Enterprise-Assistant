#!/usr/bin/env python3
"""
check_llm_api.py — 可复用的 LLM API 型号检测工具
================================================
用途：检测当前 .env 配置指向的 LLM API 真实情况，包括：
  - API Base URL（判断走的是哪家服务商）
  - 配置的模型名称
  - API 连通性测试（发送一条最小化请求）
  - 模型返回的自我描述（让模型自己说出身份）
  - 列出该 Base URL 下可用的模型列表

用法：
  cd <项目根目录>
  python tools/check_llm_api.py

依赖：openai（已在 requirements.txt 中）、python-dotenv
"""

from __future__ import annotations
import os
import sys
import json
from pathlib import Path

# ── 自动定位项目根目录并加载 .env ────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=True)
except ImportError:
    print("[WARN] python-dotenv 未安装，将直接读取系统环境变量")

try:
    from openai import OpenAI
except ImportError:
    print("[ERROR] openai 库未安装，请执行: pip install openai")
    sys.exit(1)


# ── 颜色输出工具 ──────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
RED    = "\033[91m"

def ok(msg):   print(f"{GREEN}  ✓ {msg}{RESET}")
def info(msg): print(f"{CYAN}  ℹ {msg}{RESET}")
def warn(msg): print(f"{YELLOW}  ⚠ {msg}{RESET}")
def err(msg):  print(f"{RED}  ✗ {msg}{RESET}")
def sep():     print(f"{BOLD}{'-' * 60}{RESET}")


def detect_provider(base_url: str) -> str:
    """根据 base_url 猜测服务商名称"""
    mapping = {
        "api.openai.com":       "OpenAI (官方)",
        "api.deepseek.com":     "DeepSeek",
        "api.anthropic.com":    "Anthropic Claude (官方)",
        "api.moonshot.cn":      "Moonshot (Kimi)",
        "api.lingyiwanwu.com":  "零一万物 (Yi)",
        "api.zhipuai.cn":       "智谱 AI (GLM)",
        "dashscope.aliyuncs.com": "阿里云 通义千问",
        "api.baichuan-ai.com":  "百川智能",
        "open.bigmodel.cn":     "智谱 BigModel",
        "api.together.xyz":     "Together AI",
        "api.groq.com":         "Groq",
        "api.perplexity.ai":    "Perplexity AI",
        "openrouter.ai":        "OpenRouter (多模型聚合)",
        "localhost":            "本地部署 (Ollama / vLLM / LM Studio 等)",
        "127.0.0.1":            "本地部署 (Ollama / vLLM / LM Studio 等)",
    }
    for key, name in mapping.items():
        if key in base_url:
            return name
    return f"未知服务商 ({base_url})"


def list_models(client: OpenAI) -> list[str]:
    """列出可用模型，不支持则返回空列表"""
    try:
        models = client.models.list()
        return sorted([m.id for m in models.data])
    except Exception as e:
        return [f"<无法获取模型列表: {e}>"] 


def probe_model(client: OpenAI, model: str) -> dict:
    """发送最小化请求，获取模型自我描述"""
    result = {"success": False, "identity": "", "raw_response": {}}
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Please answer in one sentence: "
                        "What is your exact model name and which company made you? "
                        "Be specific, no disclaimers."
                    ),
                }
            ],
            max_tokens=100,
            temperature=0,
        )
        result["success"] = True
        result["identity"] = response.choices[0].message.content.strip()
        result["raw_response"] = {
            "model":             response.model,
            "id":                response.id,
            "usage": {
                "prompt_tokens":     response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens":      response.usage.total_tokens,
            },
            "finish_reason": response.choices[0].finish_reason,
        }
    except Exception as e:
        result["error"] = str(e)
    return result


def main():
    print()
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}   LLM API 型号检测工具   {RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}")
    print()

    # ── 1. 读取配置 ──────────────────────────────────────────────
    api_key  = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model    = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    print(f"{BOLD}[ 1/4 ] 读取 .env 配置{RESET}")
    sep()
    info(f"API Base URL : {base_url}")
    info(f"配置模型名称 : {model}")
    info(f"API Key 状态 : {'已设置 (' + api_key[:8] + '...)' if api_key else '未设置！'}")
    info(f"推测服务商   : {detect_provider(base_url)}")
    print()

    if not api_key:
        err("OPENAI_API_KEY 未设置，无法继续检测。请检查 .env 文件。")
        sys.exit(1)

    # ── 2. 初始化客户端 ──────────────────────────────────────────
    client = OpenAI(api_key=api_key, base_url=base_url)

    # ── 3. 列出可用模型 ──────────────────────────────────────────
    print(f"{BOLD}[ 2/4 ] 列出该 API 下可用模型{RESET}")
    sep()
    models = list_models(client)
    if models:
        for m in models:
            symbol = "★" if m == model else " "
            color = GREEN if m == model else RESET
            print(f"  {color}{symbol} {m}{RESET}")
        print()
        ok(f"共找到 {len(models)} 个模型，当前配置使用: {model}")
    print()

    # ── 4. 连通性 + 模型自我描述 ─────────────────────────────────
    print(f"{BOLD}[ 3/4 ] 发送探测请求（模型自我描述）{RESET}")
    sep()
    info(f"正在向 {base_url} 发送请求，使用模型: {model} ...")
    result = probe_model(client, model)
    print()

    if result["success"]:
        ok("API 连通正常")
        print()
        print(f"{BOLD}  模型自我描述:{RESET}")
        print(f"  {YELLOW}{result['identity']}{RESET}")
        print()
        rr = result["raw_response"]
        print(f"{BOLD}[ 4/4 ] 响应元数据{RESET}")
        sep()
        info(f"响应中的 model 字段 : {rr['model']}")
        info(f"请求 ID              : {rr['id']}")
        info(f"Token 用量           : prompt={rr['usage']['prompt_tokens']}, "
             f"completion={rr['usage']['completion_tokens']}, "
             f"total={rr['usage']['total_tokens']}")
        info(f"结束原因             : {rr['finish_reason']}")
        print()
        print(f"{BOLD}{GREEN}{'=' * 60}{RESET}")
        print(f"{BOLD}{GREEN}  检测结论{RESET}")
        print(f"{BOLD}{GREEN}{'=' * 60}{RESET}")
        print(f"  服务商     : {detect_provider(base_url)}")
        print(f"  配置模型   : {model}")
        print(f"  响应模型   : {rr['model']}")
        if model != rr['model']:
            warn(f"注意：配置模型名与响应模型名不一致！")
            warn(f"  配置: {model}  →  实际响应: {rr['model']}")
        else:
            ok("配置模型名与响应模型名一致")
        print(f"{BOLD}{GREEN}{'=' * 60}{RESET}")
    else:
        err(f"API 请求失败: {result.get('error', '未知错误')}")
        print()
        err("请检查：")
        err("  1. OPENAI_API_KEY 是否正确")
        err("  2. OPENAI_BASE_URL 是否可访问")
        err("  3. OPENAI_MODEL 是否为该服务商支持的模型名")
        sys.exit(1)

    print()


if __name__ == "__main__":
    main()
