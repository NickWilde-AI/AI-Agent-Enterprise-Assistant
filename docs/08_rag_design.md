# RAG 设计说明

## 数据准备
- 文档类型：Markdown/TXT/Docx（制度、FAQ、设备巡检、项目快报、项目需求分析）
- 示例文档：
  - `data/policy_reimbursement.md`
  - `data/policy_leave.md`
  - `data/it_faq.md`
  - `data/equipment_guide.txt`
  - `data/project_status.md`
  - `data/人工智能+制造场景建设项目材料.docx`
  - `data/XX智能基于大模型应用开发需求分析和报价方案6-8.docx`

## 切分策略
- 采用 SentenceSplitter
- chunk_size=512, chunk_overlap=80
- 兼顾制度类条款的完整性与召回粒度

## 向量与索引
- 向量化：默认使用 MockEmbedding（避免 DeepSeek embeddings 404）
- 索引：VectorStoreIndex（本地 JSON 持久化）
- 索引目录：`outputs/rag_index`

## 检索策略
- similarity_top_k=3
- 输出包含引用来源（文件名 + 段落片段）

## 质量控制
- 提示中强调“依据与引用”
- 迭代计划中加入 rerank 与去重（见 `docs/07_iteration_plan.md`）

## 说明
- Docx 由 `SimpleDirectoryReader` 直接读取并进入索引。
- 若需真实 embeddings，可将 `OPENAI_EMBED_MODEL` 替换为可用的 DeepSeek embedding 模型，并重建索引。
