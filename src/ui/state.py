import os
import threading
from src.rag.indexer   import RAGIndexer
from src.rag.responder import RAGResponder

RAW_DIR  = "data/raw"
PROC_DIR = "data/processed"
MODEL    = "models/mistral-7b-instruct-v0.1.Q4_K_M.gguf"

# stato globale
state = {
    "responder":     None,
    "indexer":       None,
    "k":              5,
    "temperature":   0.0,
    "max_tokens":   512,
    "stop_sequence":"\n\n",
    "prompt_template":
      "Contesto:\n{context}\n\nDomanda: {query}\nRisposta:",
    "chunk_size":   1000,
    "chunk_overlap":200,
    "use_rag": True,
    "lock":           threading.Lock()     
}

def init_indexer():
    if state["indexer"] is None:
        state["indexer"] = RAGIndexer(
            chunk_size=state["chunk_size"],
            chunk_overlap=state["chunk_overlap"]
        )
    return state["indexer"]

def init_responder():
    if state["responder"] is None:
        state["responder"] = RAGResponder(
            model_path=MODEL,
            index_p=os.path.join(PROC_DIR, "faiss_index.bin"),
            meta_p =os.path.join(PROC_DIR, "metadata.pkl"),
            prompt_template=state["prompt_template"],
            temperature=state["temperature"],
            max_tokens=state["max_tokens"],
            stop_sequences=[state["stop_sequence"]]
        )
    return state["responder"]
