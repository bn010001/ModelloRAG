import pickle
import faiss
import numpy as np
from langchain_community.llms import LlamaCpp
from langchain_community.embeddings import SentenceTransformerEmbeddings

class RAGResponder:
    def __init__(
        self,
        model_path: str,
        index_p:    str = "data/index/faiss_index.bin",
        meta_p:     str = "data/index/metadata.pkl",
        prompt_template: str = None,
        temperature:     float = 0.0,
        max_tokens:      int  = 150,  
        stop_sequences:  list[str] = None,
        n_ctx:      int   = 2048,
        threads:    int   = 4
    ):
        # → Salva i parametri dinamici
        self.prompt_template = prompt_template or (
            "Contesto:\n{context}\n\nDomanda: {query}\nRisposta:"
        )
        self.temperature    = temperature
        self.max_tokens     = max_tokens
        self.stop_sequences = stop_sequences or ["\n\n"]

        # 1) Istanzia LLM con i parametri  
        self.llm = LlamaCpp(
            model_path=model_path,
            n_ctx=n_ctx,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=self.stop_sequences,
            n_threads=threads,
            streaming=False,
        )

        # 2) Carica FAISS + metadati  
        self.index = faiss.read_index(index_p)
        print("Numero totale di vettori indicizzati:", self.index.ntotal)
        with open(meta_p, "rb") as f:
            self.meta = pickle.load(f)

        # 3) Embedder  
        self.embedder = SentenceTransformerEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

    def retrieve(self, query: str, k: int = 5):
        emb = np.array(
            self.embedder.embed_query(query),
            dtype="float32"
        ).reshape(1, -1)
        faiss.normalize_L2(emb)
        D, I = self.index.search(emb, k)

        docs = []
        for dist, idx in zip(D[0], I[0]):
            chunk = self.meta[idx]
            docs.append({
                "text":   chunk["text"],
                "source": chunk.get("source", ""),
                "score":  float(dist)
            })
        return docs

    def answer(
        self,
        query:    str,
        with_rag: bool = True,
        k:        int  = 3
    ) -> str:
        if with_rag:
            docs = self.retrieve(query, k)
            # monta il contesto
            context = ""
            for d in docs:
                snippet = d["text"].replace("\n", " ")[:200]
                context += f"- (score={d['score']:.3f}) {snippet}…\n"
            # usa il template dinamico
            prompt = self.prompt_template.format(
                context=context,
                query=query
            )
        else:
            prompt = f"Domanda: {query}\nRisposta:"

        print("→ Prompt inviato:")
        print(prompt)
        print("→ Fine prompt\n")

        print(f"→ Prompt ({len(prompt)} chars):\n{prompt[:800]}...\n---")

        # invoca l’LLM
        return self.llm.invoke(prompt)
