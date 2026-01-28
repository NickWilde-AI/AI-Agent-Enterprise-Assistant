import argparse
import logging
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.common.config import INDEX_DIR, setup_llama_index_settings
from llama_index.core import StorageContext, load_index_from_storage

logging.basicConfig(level=logging.ERROR, stream=sys.stdout)


def query_index(query_text: str):
    """加载索引并执行查询。"""
    if not INDEX_DIR.exists():
        print(f"错误：索引目录不存在：{INDEX_DIR}")
        print("请先运行：python src/rag/build_index.py")
        sys.exit(1)

    print("🚀 Configuring RAG environment...")
    setup_llama_index_settings()
    
    # 加载本地索引
    print("📂 Loading index from storage...")
    storage_context = StorageContext.from_defaults(persist_dir=str(INDEX_DIR))
    index = load_index_from_storage(storage_context)
    
    # 执行检索（top_k=3）
    query_engine = index.as_query_engine(similarity_top_k=3)
    response = query_engine.query(query_text)
    
    print("\n" + "="*50)
    print(f"🔎 Query: {query_text}")
    print("="*50)
    print(f"\n💡 Answer:\n{response}\n")
    print("-" * 50)
    print("📚 来源：")
    for i, node in enumerate(response.source_nodes, 1):
        meta = node.node.metadata
        file_name = meta.get("file_name", "unknown")
        score = node.score if node.score else 0.0
        content_snippet = node.node.get_text().strip().replace("\n", " ")[:150]
        print(f"[{i}] {file_name} (Score: {score:.4f})")
        print(f"    片段: {content_snippet}...")
        print("")


def main():
    parser = argparse.ArgumentParser(description="查询企业知识库")
    parser.add_argument("query", type=str, help="你要查询的问题")
    args = parser.parse_args()
    
    query_index(args.query)


if __name__ == "__main__":
    main()
