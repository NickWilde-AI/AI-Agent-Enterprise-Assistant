
import sys
import logging
from llama_index.core import VectorStoreIndex, Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
from llama_index.core import StorageContext, load_index_from_storage

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def test():
    print("Init embedding...")
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5")
    Settings.embed_model = embed_model
    print("Embedding init done.")
    
    print("Creating dummy index...")
    docs = [Document(text="This is a test")]
    index = VectorStoreIndex.from_documents(docs)
    print("Index created.")
    
    print("Querying...")
    engine = index.as_query_engine()
    print(engine.query("test"))

if __name__ == "__main__":
    test()
