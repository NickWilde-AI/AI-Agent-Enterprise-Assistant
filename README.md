# 🚀 Enterprise AI Agent System (Pro Edition)

> **基于 DeepSeek-V3 + RAG + MCP 的企业级智能业务助理**

[![Status](https://img.shields.io/badge/Status-Production-success)](https://github.com/your-repo)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![LLM](https://img.shields.io/badge/LLM-DeepSeek--V3-purple)](https://deepseek.com)
[![Framework](https://img.shields.io/badge/Framework-LangChain%20%7C%20LlamaIndex-green)](https://langchain.com)

本系统是一个面向企业级场景的智能业务助理，深度集成了 **RAG (检索增强生成)**、**Contextual Memory (上下文记忆)** 和 **MCP (模型上下文协议)**。它不仅能精准回答文档问题，还能通过工具调用直接办理业务，是企业数字化转型的得力助手。

---

## ✨ 核心功能 (Key Features)

### 1. 🧠 具备“超级记忆”的对话 (Contextual Memory)
- **[NEW] 多轮对话支持**：系统能够记住聊天的上下文。
  - *User*: "帮我查一下张三的项目进度。"
  - *Agent*: "张三当前负责‘阿波罗计划’，进度 80%。"
  - *User*: "**这个项目**有什么风险？" (系统自动理解“这个项目”指“阿波罗计划”)
  - *Agent*: "‘阿波罗计划’的主要风险是..."

### 2. 📚 多源异构 RAG 检索
- **全格式支持**：深度解析 Word (`.docx`)、PDF (`.pdf`)、Markdown (`.md`) 等非结构化文档。
- **[独家] 复杂表格理解**：内置 `ExcelMarkdownReader`，完美还原 Excel (`.xlsx`) 的行列语义，精准回答类似“查找第三季度财务报表中的研发支出”等复杂查询。
- **全局认知**：自动生成知识库摘要，Agent 清楚“我有哪些文件”、“我可以回答哪类问题”。

### 3. 🛠️ MCP 标准化工具调用 (Tools)
- **业务系统打通**：通过 MCP 协议连接企业内部数据库与 API。
- **开箱即用工具**：
  - `get_employee_profile`: 员工信息查询
  - `get_reimbursement`: 财务报销数据实时调取
  - `create_ticket`: 自动化工单创建

---

## 💻 快速启动 (Quick Start)

### 1. 环境准备
确保已安装 Python 3.10+。

```bash
# 1. 克隆项目 (示例)
git clone https://github.com/your-username/AI-Agent-Enterprise-Assistant.git
cd AI-Agent-Enterprise-Assistant

# 2. 运行安装脚本 (自动创建 venv 并安装依赖)
chmod +x setup.sh
./setup.sh
```

### 2. 配置密钥
创建 `.env` 文件并填入 DeepSeek/OpenAI 密钥：
```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

### 3. 构建知识库
解析 `data/` 目录下的所有企业文档：
```bash
source venv/bin/activate
python src/rag/build_index.py
```

### 4. 启动应用
```bash
streamlit run src/app/streamlit_app.py
```
> 访问浏览器：[http://localhost:8501](http://localhost:8501)

---

## 🏗️ 系统架构

| 模块 | 技术栈 | 说明 |
| :--- | :--- | :--- |
| **Frontend** | Streamlit | 极简交互界面，支持流式输出 |
| **Brain (Agent)** | LangChain | ReAct 思考模式，负责意图识别与工具分发 |
| **Memory** | Streamlit Session | 本地会话级记忆存储 |
| **Knowledge** | LlamaIndex | 高效向量检索，支持混合检索策略 |
| **Tools** | MCP Protocol | 标准化工具接口，解耦业务逻辑 |

---

## 📂 目录结构

```text
.
├── data/               # 企业私有数据 (Excel, PDF, SQLite)
├── src/
│   ├── app/            # Streamlit 前端应用
│   ├── agent/          # Agent 核心编排 (with Memory)
│   ├── rag/            # 索引构建与检索逻辑
│   └── mcp_server/     # 业务工具集 (Tools)
├── outputs/            # 向量索引持久化存储
├── requirements.txt    # 项目依赖
└── README.md           # 说明文档
```
