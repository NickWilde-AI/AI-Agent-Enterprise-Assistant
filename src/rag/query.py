
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add src to path to ensure imports work if run from different dirs
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.core.embeddings import MockEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# Load env variables
load_dotenv(ROOT / ".env", override=True)
INDEX_DIR = ROOT / "outputs" / "rag_index"

import logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if not value and default is None:
        print(f"WARNING: Environment variable {name} not found!")
    return value if value else default

def setup_rag():
    """Configure RAG settings (must match build_index.py)."""
    api_key = _get_env("OPENAI_API_KEY")
    api_base = _get_env("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    llm_model = _get_env("OPENAI_MODEL", "deepseek-chat")
    embed_model = _get_env("OPENAI_EMBED_MODEL", "mock")

    # Embedding setup
    if embed_model == "mock":
        Settings.embed_model = MockEmbedding(embed_dim=384)
    elif embed_model.startswith("local:"):
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        model_name = embed_model.split("local:")[1]
        print(f"Loading local embedding model: {model_name}...")
        # Suppress some HF warnings
        Settings.embed_model = HuggingFaceEmbedding(model_name=model_name)
        print("Embedding model loaded.")
    else:
        Settings.embed_model = OpenAIEmbedding(
            model=embed_model,
            api_key=api_key,
            api_base=api_base,
        )

    # LLM setup
    try:
        from llama_index.llms.deepseek import DeepSeek
        Settings.llm = DeepSeek(
            model=llm_model,
            api_key=api_key,
            api_base=api_base,
        )
    except ImportError:
        # Fallback to OpenAI-like if DeepSeek package issue, but set context window manually to avoid validation error
        from llama_index.llms.openai_like import OpenAILike
        Settings.llm = OpenAILike(
            model=llm_model,
            api_key=api_key,
            api_base=api_base,
            is_chat_model=True,
            context_window=4096 
        )

def query_index(query_text: str):
    """Load index and query."""
    if not INDEX_DIR.exists():
        print(f"Error: Index directory not found at {INDEX_DIR}")
        print("Please run 'python src/rag/build_index.py' first.")
        sys.exit(1)

    setup_rag()
    
    # Load index
    storage_context = StorageContext.from_defaults(persist_dir=str(INDEX_DIR))
    index = load_index_from_storage(storage_context)
    
    # Query
    query_engine = index.as_query_engine(similarity_top_k=3)
    response = query_engine.query(query_text)
    
    print("\n" + "="*50)
    print(f"🔎 Query: {query_text}")
    print("="*50)
    print(f"\n💡 Answer:\n{response}\n")
    print("-" * 50)
    print("📚 Sources:")
    for i, node in enumerate(response.source_nodes, 1):
        meta = node.node.metadata
        file_name = meta.get("file_name", "unknown")
        score = node.score if node.score else 0.0
        content_snippet = node.node.get_text().strip().replace("\n", " ")[:150]
        print(f"[{i}] {file_name} (Score: {score:.4f})")
        print(f"    Content: {content_snippet}...")
        print("")

def main():
    parser = argparse.ArgumentParser(description="Query the Enterprise Knowledge Base")
    parser.add_argument("query", type=str, help="The question you want to ask")
    args = parser.parse_args()
    
    query_index(args.query)

if __name__ == "__main__":
    main()
