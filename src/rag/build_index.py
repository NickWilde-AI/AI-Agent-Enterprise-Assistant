from __future__ import annotations

import os

from dotenv import load_dotenv
from pathlib import Path

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document
import pandas as pd
from typing import List, Any

ROOT = Path(__file__).resolve().parents[2]
# 自动读取 .env，避免每次手动设置环境变量。
load_dotenv(ROOT / ".env")
DATA_DIR = ROOT / "data"
INDEX_DIR = ROOT / "outputs" / "rag_index"


def _get_env(name: str, default: str | None = None) -> str | None:
    """读取环境变量，若未设置则返回默认值。"""
    value = os.getenv(name)
    return value if value else default


class ExcelMarkdownReader(BaseReader):
    """Custom reader to convert Excel files to Markdown tables."""
    def load_data(self, file: Path, extra_info: dict = None) -> List[Document]:
        try:
            # Read all sheets
            dfs = pd.read_excel(file, sheet_name=None)
            text_parts = []
            for sheet_name, df in dfs.items():
                text_parts.append(f"### Sheet: {sheet_name}")
                # Convert to markdown
                text_parts.append(df.to_markdown(index=False))
                text_parts.append("\n")
            
            content = "\n".join(text_parts)
            return [Document(text=content, metadata=extra_info or {})]
        except Exception as e:
            print(f"Error reading Excel file {file}: {e}")
            return []

def build_index() -> None:
    """构建 RAG 索引：读取数据、切分、向量化，并持久化到 outputs/rag_index。"""
    # 读取 data/ 下的文档（支持 md/txt/docx/xlsx）。
    # 使用自定义 Excel 解析器
    file_extractor = {
        ".xlsx": ExcelMarkdownReader()
    }
    
    documents = SimpleDirectoryReader(
        input_dir=str(DATA_DIR),
        required_exts=[".md", ".txt", ".docx", ".xlsx", ".doc"],
        recursive=True,
        file_extractor=file_extractor
    ).load_data()

    # Create a summary document of all files
    file_list = []
    for doc in documents:
        if "file_name" in doc.metadata:
            file_list.append(doc.metadata["file_name"])
    
    # Deduplicate file names (documents are chunks)
    unique_files = sorted(list(set(file_list)))
    
    summary_text = "# 知识库文件目录\n\n以下是本知识库中包含的所有文件列表：\n\n"
    for f in unique_files:
        summary_text += f"- {f}\n"
    
    summary_text += f"\n总计文件数量：{len(unique_files)} 个。\n"
    
    print("Injecting summary document with content:")
    print(summary_text)
    
    summary_doc = Document(
        text=summary_text,
        metadata={"file_name": "SYSTEM_INDEX_SUMMARY.md", "category": "system"}
    )
    documents.append(summary_doc)

    # 读取模型配置（默认 DeepSeek，embedding 默认 mock）。
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
        Settings.embed_model = HuggingFaceEmbedding(model_name=model_name)
    else:
        Settings.embed_model = OpenAIEmbedding(
            model=embed_model,
            api_key=api_key,
            api_base=api_base,
        )
    # 设置 LLM（用于后续响应生成时的默认模型配置）。
    Settings.llm = OpenAI(
        model=llm_model,
        api_key=api_key,
        api_base=api_base,
    )
    # 文本切分器：控制块大小与重叠，平衡检索粒度与上下文完整度。
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=80)

    # 构建向量索引并持久化到 outputs/rag_index。
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=str(INDEX_DIR))


if __name__ == "__main__":
    build_index()
    print(f"Index built at {INDEX_DIR}")
