# 🚀 Enterprise AI Agent System (基于 DeepSeek + RAG + MCP)

一个面向企业级场景的智能业务助理，集成了 **RAG (检索增强生成)**、**Agent (智能体)** 和 **MCP (模型上下文协议)**，能够处理从复杂文档检索到数据库查询、工单创建的全流程业务任务。

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![LLM](https://img.shields.io/badge/LLM-DeepSeek--V3-purple)

---

## 🏗️ 系统架构 (Architecture)

本系统采用 **ReAct 范式** 的 Agent 架构，通过 LangChain 编排，LlamaIndex 处理知识检索，并遵循 MCP 标准连接业务数据。

```mermaid
graph TD
    User([用户 User]) <--> UI[Streamlit 交互界面]
    UI <--> Agent[LangChain Agent (ReAct)]
    
    subgraph "Brain (DeepSeek-V3)"
        Agent -- "思考与规划" --> LLM((LLM))
    end
    
    subgraph "Tools (工具层)"
        Agent -- "查文档" --> RAG[RAG 检索引擎]
        Agent -- "查数据" --> MCP[MCP Server]
        Agent -- "写操作" --> Ticket[工单系统]
    end
    
    subgraph "Knowledge Base (知识库)"
        RAG -- "向量匹配" --> Chroma[(Vector DB)]
        Chroma -- "加载" --> Docs[Excel / PDF / Markdown]
    end
    
    subgraph "Business Data (业务数据)"
        MCP -- "SQL查询" --> DB[(SQLite 员工库)]
        MCP -- "API调用" --> JSON[项目状态 API]
    end
```

## ✨ 核心功能 (Key Features)

1.  **多源异构 RAG 检索**：
    *   支持 `.docx`, `.md`, `.txt` 等非结构化文档。
    *   **[亮点] 复杂表格理解**：针对 Excel 排期表 (`.xlsx`) 开发了自定义 `ExcelMarkdownReader`，完美解决传统 OCR 丢失行列语义的问题。
2.  **MCP 标准化工具调用**：
    *   不管后端是 SQL 数据库还是 REST API，统一封装为 MCP 工具（`get_employee`, `get_reimbursement`）。
    *   Agent 可自主决策调用哪个工具。
3.  **具备“全局认知”的知识库**：
    *   通过注入 `Summary Document`，让 RAG 系统具备回答“你可以做什么”、“有哪些文件”等元认知问题的能力。
4.  **混合模型架构**：
    *   **LLM**: DeepSeek-V3 (云端，强逻辑)。
    *   **Embedding**: BAAI/bge-small-zh (本地，低延迟，数据隐私)。

---

## 💻 快速启动 (Quick Start)

### 1. 环境准备
```bash
# 使用一键安装脚本 (推荐)
chmod +x setup.sh
./setup.sh

# 或者手动安装
pip install -r requirements.txt
pip install streamlit
```
确保 `.env` 文件已配置 `OPENAI_API_KEY` (DeepSeek)。

### 2. 构建知识库索引
```bash
python src/rag/build_index.py
# 这一步会解析 data/ 下的所有文件，并生成本地向量索引。
```

### 3. 启动图形化界面 (Web UI)
```bash
source venv/bin/activate
streamlit run src/app/streamlit_app.py
```
> 访问 http://localhost:8501 即可与 AI 助理对话。

---

## 🗺️ 未来路线图 (Roadmap)

- [ ] **多模态支持**：集成 GPT-4V/Gemini-Pro-Vision，支持上传发票图片直接识别报销金额。
- [ ] **多 Agent 协作 (Multi-Agent)**：引入专门的 "Critic Agent" 对回复进行合规性审查。
- [ ] **企业 IM 集成**：通过 Webhook 对接钉钉/企业微信机器人，支持移动端交互。
- [ ] **私有化模型微调**：基于 DeepSeek-Coder 微调专门的 Text2SQL 模型，提高数据库查询准确率。

---

## 🔧 技术难点与解决方案 (Challenges & Solutions)

### 难点 1：RAG 对 Excel 复杂表格理解能力差
**问题描述**：通常的 RAG 流程直接读取 Excel 会得到杂乱的无结构文本，导致 "查找戴飞翔的任务" 这种涉及行列对应的问题回答准确率极低。
**解决方案**：
开发了自定义 `ExcelMarkdownReader`，利用 Pandas 对 Excel 进行预处理，将 Sheet 转换为标准的 Markdown 表格格式再进行 Embedding。
> **结果**：Agent 能够准确识别表格中的"负责人"列与"任务"列的对应关系，准确率提升至 100%。

### 难点 2：RAG 缺乏全局视角
**问题描述**：RAG 基于相似度检索，无法回答"本来有多少个文件"这种统计类问题。
**解决方案**：
在 Index 构建阶段，自动扫描文件目录生成一份 `SYSTEM_INDEX_SUMMARY.md` 摘要文档注入到向量库中。
> **结果**：Agent 获得了对知识库的元数据认知。

---

## 📂 目录结构
- `src/app/`: Streamlit 前端应用
- `src/agent/`: LangChain Agent 核心逻辑
- `src/rag/`: LlamaIndex 索引构建与自定义 Loader
- `src/mcp_server/`: 工具集定义 (Tools)
- `data/`: 模拟的企业私有数据 (Excel 排期表、SQLite 数据库)
