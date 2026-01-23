
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT / "src"))

from agent.agent_workflow import rag_search

def verify_fix():
    print("Verifying RAG with DeepSeek + Local Embeddings...")
    # Query logic
    query = "数字人有哪些功能？" 
    try:
        result = rag_search(query)
        print(f"\nQuery: {query}")
        print(f"Result (First 500 chars): {result[:500]}")
        if "unknown" in result and len(result) < 100:
             print("WARNING: Result seems empty or invalid.")
        else:
             print("SUCCESS: Retrieved content from knowledge base.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    verify_fix()
