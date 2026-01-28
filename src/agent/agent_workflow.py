from __future__ import annotations

import json
import sys
from typing import Any

import anyio
from langchain.agents import AgentExecutor
from langchain.agents.structured_chat.output_parser import StructuredChatOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pathlib import Path
from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage

# Import from centralized config
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.common.config import INDEX_DIR, get_env, setup_llama_index_settings

# Delayed import for MCP tools
sys.path.insert(0, str(ROOT / "src" / "mcp_server"))
import server as mcp_server  # noqa: E402

from mcp.client.session import ClientSession

_GLOBAL_INDEX = None


def _load_index() -> VectorStoreIndex:
    """加载 RAG 索引并配置向量模型（带全局缓存）。"""
    global _GLOBAL_INDEX
    if _GLOBAL_INDEX is not None:
        return _GLOBAL_INDEX

    print("🚀 Loading RAG Index and Embedding Model...")
    # Centralized Settings setup
    setup_llama_index_settings()

    # 从本地磁盘加载向量索引
    storage_context = StorageContext.from_defaults(persist_dir=str(INDEX_DIR))
    _GLOBAL_INDEX = load_index_from_storage(storage_context)
    print("✅ Index loaded.")
    return _GLOBAL_INDEX


def rag_search(query: str) -> str:
    """RAG 检索入口，返回答案与来源（JSON 字符串）。"""
    index = _load_index()
    engine = index.as_query_engine(similarity_top_k=5)
    response = engine.query(query)
    sources = []
    for node in response.source_nodes:
        meta = node.node.metadata
        file_name = meta.get("file_name", "unknown")
        snippet = node.node.get_text().strip().replace("\n", " ")[:120]
        sources.append(f"{file_name}: {snippet}...")
    payload = {"answer": str(response), "sources": sources}
    return json.dumps(payload, ensure_ascii=False)


def _call_mcp_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """在进程内调用 MCP 工具，返回结构化结果。"""
    async def _run() -> dict[str, Any]:
        client_to_server_send, client_to_server_recv = anyio.create_memory_object_stream(1)
        server_to_client_send, server_to_client_recv = anyio.create_memory_object_stream(1)

        async def run_server() -> None:
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
        StructuredTool.from_function(mcp_get_reimbursement_summary, name="get_reimbursement_summary", description="查询员工某月报销总额与明细"),
        StructuredTool.from_function(mcp_get_project_status, name="get_project_status", description="查询项目进度与风险"),
        StructuredTool.from_function(mcp_create_ticket, name="create_ticket", description="创建工单记录"),
    ]

    api_key = get_env("OPENAI_API_KEY")
    api_base = get_env("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    llm_model = get_env("OPENAI_MODEL", "deepseek-chat")

    llm = ChatOpenAI(
        model=llm_model,
        temperature=0.2,
        api_key=api_key,
        base_url=api_base,
    )
    
    output_parser = StructuredChatOutputParser()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是腾讯企业内部的智能文档与业务专家。你的目标是帮助员工高效利用知识库和业务数据。\n"
                "行为准则：\n"
                "1. **文档问答**：用户询问关于“文档内容、技术方案、白皮书、讲义”等问题时，请务必使用 `rag_search` 工具检索相关信息，并基于检索结果回答。\n"
                "2. **拒绝纯闲聊**：仅在用户询问与工作/文档完全无关的通用话题（如“今天天气”、“讲个笑话”）时才拒绝。\n"
                "3. **严谨查数**：涉及报销金额、人员信息等精确数据，必须调用 Database 工具，禁止编造。\n"
                "\n"
                "可用工具如下（名称列表：{tool_names}）：\n{tools}\n\n"
                "{format_instructions}",
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("assistant", "{agent_scratchpad}"),
        ]
    ).partial(format_instructions=output_parser.get_format_instructions())

    from langchain.agents.format_scratchpad import format_log_to_str
    from langchain.tools.render import render_text_description
    
    tool_strings = render_text_description(tools)
    tool_names = ", ".join([t.name for t in tools])
    prompt = prompt.partial(tools=tool_strings, tool_names=tool_names)
    
    agent = (
        {
            "input": lambda x: x["input"],
            "chat_history": lambda x: x.get("chat_history", []),
            "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
        }
        | prompt
        | llm
        | output_parser
    )
    
    return AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True)


def run(user_input: str) -> None:
    executor = build_agent()
    result = executor.invoke({"input": user_input})
    print(result["output"])


if __name__ == "__main__":
    run("请帮我查询张三在 2025-03 的报销总额并生成一封给HR的说明邮件。")
