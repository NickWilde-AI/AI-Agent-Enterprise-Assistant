from __future__ import annotations
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base paths
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
INDEX_DIR = ROOT / "outputs" / "rag_index"
DB_PATH = ROOT / "company.db"
PROJECT_STATUS_PATH = ROOT / "project_status.json"
TICKETS_PATH = ROOT / "outputs" / "tickets.json"

# Load environment variables once
load_dotenv(ROOT / ".env", override=True)

def get_env(name: str, default: str | None = None) -> str | None:
    """Get an environment variable or return default."""
    return os.getenv(name, default)

def setup_llama_index_settings():
    """Shared configuration for LlamaIndex Settings (LLM & Embeddings)."""
    from llama_index.core.settings import Settings
    from llama_index.core.embeddings import MockEmbedding
    from llama_index.embeddings.openai import OpenAIEmbedding
    
    api_key = get_env("OPENAI_API_KEY")
    api_base = get_env("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    llm_model = get_env("OPENAI_MODEL", "deepseek-chat")
    embed_model = get_env("OPENAI_EMBED_MODEL", "mock")

    # Configure Embedding Model
    if embed_model == "mock":
        Settings.embed_model = MockEmbedding(embed_dim=384)
    elif embed_model.startswith("local:"):
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        model_name = embed_model.split("local:")[1]
        # Use a singleton pattern implicitly via internal cache or just re-init
        # HuggingFaceEmbedding usually caches model weights
        Settings.embed_model = HuggingFaceEmbedding(model_name=model_name, device="cpu")
    else:
        Settings.embed_model = OpenAIEmbedding(
            model=embed_model,
            api_key=api_key,
            api_base=api_base,
        )

    # Configure LLM
    try:
        from llama_index.llms.deepseek import DeepSeek
        Settings.llm = DeepSeek(model=llm_model, api_key=api_key, api_base=api_base)
    except ImportError:
        from llama_index.llms.openai import OpenAI
        Settings.llm = OpenAI(model=llm_model, api_key=api_key, api_base=api_base)
    
    return Settings
