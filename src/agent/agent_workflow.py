from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import anyio
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.agents.structured_chat.output_parser import StructuredChatOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.tools import StructuredTool
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.settings import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from mcp.client.session import ClientSession

ROOT = Path(__file__).resolve().parents[2]
# 自动读取 .env，避免每次手动设置环境变量。
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT / "src" / "mcp_server"))
import server as mcp_server  # noqa: E402

INDEX_DIR = ROOT / "outputs" / "rag_index"
_GLOBAL_INDEX = None


def _get_env(name: str, default: str | None = None) -> str | None:
    """读取环境变量，若未设置则返回默认值。"""
    value = os.getenv(name)
    return value if value else default

def _load_index() -> VectorStoreIndex:
    """加载 RAG 索引并配置向量模型。"""
    global _GLOBAL_INDEX
    if _GLOBAL_INDEX is not None:
        return _GLOBAL_INDEX

    print("🚀 Loading RAG Index and Embedding Model...")
    api_key = _get_env("OPENAI_API_KEY")
    api_base = _get_env("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    llm_model = _get_env("OPENAI_MODEL", "deepseek-chat")
    embed_model = _get_env("OPENAI_EMBED_MODEL", "mock")

    # 设置向量模型
    if embed_model == "mock":
        Settings.embed_model = MockEmbedding(embed_dim=384)
    elif embed_model.startswith("local:"):
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        model_name = embed_model.split("local:")[1]
        Settings.embed_model = HuggingFaceEmbedding(model_name=model_name, device="cpu")
    else:
        Settings.embed_model = OpenAIEmbedding(
            model=embed_model,
            api_key=api_key,
            api_base=api_base,
        )
    # 设置默认 LLM 配置
    try:
        from llama_index.llms.deepseek import DeepSeek
        Settings.llm = DeepSeek(model=llm_model, api_key=api_key, api_base=api_base)
    except ImportError:
        from llama_index.llms.openai import OpenAI
        Settings.llm = OpenAI(model=llm_model, api_key=api_key, api_base=api_base)

    storage_context = StorageContext.from_defaults(persist_dir=str(INDEX_DIR))
    _GLOBAL_INDEX = load_index_from_storage(storage_context)
    print("✅ Index loaded.")
    return _GLOBAL_INDEX


def rag_search(query: str) -> str:
    """RAG 检索入口，返回答案与来源（JSON 字符串）。"""
    index = _load_index()
    engine = index.as_query_engine(similarity_top_k=3)
    response = engine.query(query)
    sources = []
    for node in response.source_nodes:
        meta = node.node.metadata
        file_name = meta.get("file_name", "unknown")
        snippet = node.node.get_text().strip().replace("\n", " ")[:120]
        sources.append(f"{file_name}: {snippet}...")
    payload = {"answer": response.response, "sources": sources}
    return json.dumps(payload, ensure_ascii=False)


def _call_mcp_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """在进程内调用 MCP 工具，返回结构化结果。"""
    async def _run() -> dict[str, Any]:
        client_to_server_send, client_to_server_recv = anyio.create_memory_object_stream(1)
        server_to_client_send, server_to_client_recv = anyio.create_memory_object_stream(1)

        async def run_server() -> None:
            """启动 MCP Server（内存流模式）。"""
            await mcp_server.mcp._mcp_server.run(
                client_to_server_recv,
                server_to_client_send,
                mcp_server.mcp._mcp_server.create_initialization_options(),
                raise_exceptions=True,
            )

        async with anyio.create_task_group() as tg:
            tg.start_soon(run_server)
            async with ClientSession(server_to_client_recv, client_to_server_send) as session:
                await session.initialize()
                result = await session.call_tool(name, args)
            tg.cancel_scope.cancel()
            return _normalize_tool_result(result)

    return anyio.run(_run)


def _normalize_tool_result(result: Any) -> dict[str, Any]:
    """将 MCP 返回值转换为可 JSON 化的字典。"""
    if isinstance(result, dict):
        return result
    if hasattr(result, "structuredContent") and result.structuredContent is not None:
        return result.structuredContent
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return {"content": str(result)}


def mcp_get_employee_profile(name: str) -> str:
    return json.dumps(_call_mcp_tool("get_employee_profile", {"name": name}), ensure_ascii=False)


def mcp_get_reimbursement_summary(name: str, month: str) -> str:
    return json.dumps(
        _call_mcp_tool("get_reimbursement_summary", {"name": name, "month": month}),
        ensure_ascii=False,
    )


def mcp_get_project_status(project: str) -> str:
    return json.dumps(_call_mcp_tool("get_project_status", {"project": project}), ensure_ascii=False)


def mcp_create_ticket(title: str, description: str, requester: str, priority: str = "P2") -> str:
    return json.dumps(
        _call_mcp_tool(
            "create_ticket",
            {
                "title": title,
                "description": description,
                "requester": requester,
                "priority": priority,
            },
        ),
        ensure_ascii=False,
    )


def build_agent() -> AgentExecutor:
    """构建支持多工具的结构化聊天 Agent。"""
    tools = [
        StructuredTool.from_function(rag_search, name="rag_search", description="检索企业知识库并返回答案与来源"),
        StructuredTool.from_function(mcp_get_employee_profile, name="get_employee_profile", description="查询员工部门和邮箱"),
        StructuredTool.from_function(
            mcp_get_reimbursement_summary,
            name="get_reimbursement_summary",
            description="查询员工某月报销总额与明细",
        ),
        StructuredTool.from_function(
            mcp_get_project_status,
            name="get_project_status",
            description="查询项目进度与风险",
        ),
        StructuredTool.from_function(
            mcp_create_ticket,
            name="create_ticket",
            description="创建工单记录",
        ),
    ]

    api_key = _get_env("OPENAI_API_KEY")
    api_base = _get_env("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    llm_model = _get_env("OPENAI_MODEL", "deepseek-chat")

    # LLM 用于工具选择与生成最终回复。
    llm = ChatOpenAI(
        model=llm_model,
        temperature=0.2,
        api_key=api_key,
        base_url=api_base,
    )
    # Structured Chat 需要格式化指令以解析工具调用的 JSON。
    output_parser = StructuredChatOutputParser()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是企业内部智能助理。凡是涉及报销金额、员工信息、项目进度的查询，"
                "必须调用对应的工具获取数据，再生成答复。\n"
                "可用工具如下（名称列表：{tool_names}）：\n{tools}\n\n"
                "{format_instructions}",
            ),
            ("human", "{input}"),
            ("assistant", "{agent_scratchpad}"),
        ]
    ).partial(format_instructions=output_parser.get_format_instructions())

    # FIX: Compatibility with newer langchain versions
    from langchain.agents.format_scratchpad import format_log_to_str
    from langchain.tools.render import render_text_description
    
    # Pre-render tool information for the prompt
    tool_strings = render_text_description(tools)
    tool_names = ", ".join([t.name for t in tools])
    prompt = prompt.partial(tools=tool_strings, tool_names=tool_names)
    
    # Manually constructing the agent to avoid version conflict with 'agent_scratchpad'
    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
        }
        | prompt
        | llm
        | output_parser
    )
    
    return AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True)


def run(user_input: str) -> None:
    """运行 Agent，并打印最终输出。"""
    executor = build_agent()
    result = executor.invoke({"input": user_input})
    print(result["output"])


if __name__ == "__main__":
    run("请帮我查询张三在 2025-03 的报销总额并生成一封给HR的说明邮件。")
