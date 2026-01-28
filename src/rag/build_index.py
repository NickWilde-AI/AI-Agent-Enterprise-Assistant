from __future__ import annotations

import sys
from pathlib import Path

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document
import pandas as pd
from typing import List

# Config import
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.common.config import DATA_DIR, INDEX_DIR, setup_llama_index_settings


class ExcelMarkdownReader(BaseReader):
    """自定义读取器：将 Excel 表格转换为 Markdown 表格文本。"""
    def load_data(self, file: Path, extra_info: dict = None) -> List[Document]:
        try:
            # 读取所有工作表，避免只索引第一个 Sheet。
            dfs = pd.read_excel(file, sheet_name=None)
            text_parts = []
            for sheet_name, df in dfs.items():
                text_parts.append(f"### Sheet: {sheet_name}")
                # 将 DataFrame 转换为 Markdown 表格，保留行列结构。
                text_parts.append(df.to_markdown(index=False))
                text_parts.append("\n")
            
            content = "\n".join(text_parts)
            return [Document(text=content, metadata=extra_info or {})]
        except Exception as e:
            print(f"读取 Excel 文件失败 {file}: {e}")
            return []

def build_index() -> None:
    """构建 RAG 索引：读取数据、切分、向量化，并持久化到 outputs/rag_index。"""
    print("🚀 Starting RAG Index Build...")
    
    # 1. 统一加载 Embedding / LLM 配置
    setup_llama_index_settings()
    
    # 2. 读取 data/ 下的文档（支持 md/txt/docx/xlsx）。
    file_extractor = {
        ".xlsx": ExcelMarkdownReader()
    }
    
    documents = SimpleDirectoryReader(
        input_dir=str(DATA_DIR),
        required_exts=[".md", ".txt", ".docx", ".xlsx", ".doc", ".pdf"],
        recursive=True,
        file_extractor=file_extractor
    ).load_data()

    # 3. 生成“知识库文件目录”摘要文档
    file_list = []
    for doc in documents:
        if "file_name" in doc.metadata:
            file_list.append(doc.metadata["file_name"])
    
    unique_files = sorted(list(set(file_list)))
    
    summary_text = "# 知识库文件目录\n\n以下是本知识库中包含的所有文件列表：\n\n"
    for f in unique_files:
        summary_text += f"- {f}\n"
    summary_text += f"\n总计文件数量：{len(unique_files)} 个。\n"
    
    print("注入摘要文档内容：")
    print(summary_text)
    
    summary_doc = Document(
        text=summary_text,
        metadata={"file_name": "SYSTEM_INDEX_SUMMARY.md", "category": "system"}
    )
    documents.append(summary_doc)

    # 4. 文本切分器
    from llama_index.core.settings import Settings
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=80)

    # 5. 构建向量索引并持久化
    print(f"Indexing {len(documents)} documents...")
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=str(INDEX_DIR))
    print(f"✅ Index built successfully at: {INDEX_DIR}")


if __name__ == "__main__":
    build_index()
