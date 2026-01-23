# Demo 证据清单

## 运行记录
- Agent 日志：`outputs/agent_demo.log`
- MCP 客户端日志：`outputs/demo_client.log`
- MCP 工具调用示例：`outputs/tool_call_log.md`
- RAG 查询日志：`outputs/rag_query.log`

## 关键截图占位
- RAG 检索回答截图：来源显示（待截图）
- MCP 工具调用截图：报销查询 + 工单创建（待截图）
- Agent 多步流程截图：报销查询 + 邮件草稿（待截图）

## 复现步骤（不含 Key）
1. `OPENAI_API_KEY` 环境变量设置为 DeepSeek Key
2. `python src/rag/build_index.py`
3. `python src/mcp_server/demo_client.py`
4. `python src/agent/agent_workflow.py`
