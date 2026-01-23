# 项目总览

## 项目题目
企业智能知识助理 & 工作流 Agent 系统（综合项目）

## 项目目标（1-2 段）
建设一个可演示的企业内部智能助理，支持知识检索、数据查询与流程草稿生成。系统聚焦制造业内部高频问题（制度、报销、项目进度、设备巡检），通过 RAG + MCP + Agent 的组合，实现“能答、能查、能办”的闭环体验。

## 阶段任务与验收标准
- Phase 0 产品定义：交付背景/画像、PRD、流程图（见 `docs/01_background_persona.md`、`docs/02_prd.md`、`docs/03_user_flow.md`）
- Phase 1 知识库：RAG 可运行、可引用来源，支持中文问答（`src/rag/`、`data/`）
- Phase 2 MCP 工具：至少 2 个工具，可被模型调用（`src/mcp_server/`、`docs/05_mcp_tools.md`）
- Phase 3 Agent 流程：多步骤任务自动拆解并调用工具（`src/agent/agent_workflow.py`）
- Phase 4 评估复盘：任务评估表、问题与迭代计划（`docs/06_eval_report.md`、`docs/07_iteration_plan.md`）

## 技术栈
- LLM：DeepSeek（OpenAI 兼容 API）
- RAG：LlamaIndex
- Agent：LangChain Structured Chat Agent
- MCP：Python SDK（FastMCP）
