# 系统整体架构（DeepSeek）

```text
                         +-------------------+
                         |   Web/CLI Client  |
                         +---------+---------+
                                   |
                                   v
                        +---------------------+
                        |  Agent Orchestrator |
                        | (LangChain Agent)   |
                        +----+-----------+----+
                             |           |
                             v           v
                 +----------------+  +------------------+
                 |   RAG Service  |  |   MCP Client     |
                 | (LlamaIndex)   |  +--------+---------+
                 +-------+--------+           |
                         |                    v
                         |           +-------------------+
                         |           |   MCP Server      |
                         |           | (Tools + DB/JSON) |
                         |           +----+---------+----+
                         |                |         |
                         v                v         v
               +----------------+   +---------+  +---------+
               | Knowledge Base |   | SQLite  |  |  JSON   |
               | (md/txt/pdf)   |   |  DB     |  | Tickets |
               +----------------+   +---------+  +---------+
                         |
                         v
                +----------------+
                | LLM/Embed API  |
                | DeepSeek       |
                +----------------+
```

## 说明
- RAG：企业文档（md/txt）索引 + 引用来源。
- MCP：提供员工、报销、项目、工单工具。
- Agent：根据用户意图决定调用 RAG 或 MCP，形成多步骤结果。
- LLM：DeepSeek（OpenAI 兼容接口），Embedding 在不支持时使用 mock 兜底。
