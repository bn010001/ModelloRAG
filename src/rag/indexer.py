# src/rag/indexer.py
import os
import json
import pickle
import faiss
import numpy as np
from glob import glob
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings

class RAGIndexer:
    def __init__(
        self,
        proc_dir:       str = "data/processed",
        index_p:        str = "data/index/faiss_index.bin",
        meta_p:         str = "data/index/metadata.pkl",
        done_p:         str = "data/index/indexed_files.json",
        chunk_size:     int = 700,
        chunk_overlap:  int = 150, 
        embed_model:    str = "all-MiniLM-L6-v2"
    ):
        self.proc_dir      = proc_dir
        self.index_p       = index_p
        self.meta_p        = meta_p
        self.done_p        = done_p
        self.chunk_size    = chunk_size
        self.chunk_overlap = chunk_overlap

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.embedder = SentenceTransformerEmbeddings(
            model_name=embed_model
        )

        # carica la lista dei file già processati
        if os.path.exists(self.done_p):
            with open(self.done_p, "r", encoding="utf-8") as f:
                self.done_files = set(json.load(f))
        else:
            self.done_files = set()

    def build(self, rebuild: bool = True):
        # trova tutti i .txt nella cartella di processamento
        all_txts = sorted(glob(os.path.join(self.proc_dir, "*.txt")))

        # decidi quali file processare
        if rebuild:
            to_process = all_txts
            self.done_files.clear()
        else:
            to_process = [
                p for p in all_txts
                if os.path.basename(p) not in self.done_files
            ]

        if not to_process:
            print("🟢 Nessun file nuovo da indicizzare.")
            return

        # chunking e raccolta dei nuovi documenti
        new_docs = []
        for path in to_process:
            base = os.path.basename(path)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            for i, chunk in enumerate(self.splitter.split_text(text)):
                new_docs.append({
                    "id":     f"{base}_c{i}",
                    "text":   chunk,
                    "source": base
                })

        # embedding e normalizzazione
        texts = [d["text"] for d in new_docs]
        embs  = np.array(self.embedder.embed_documents(texts), dtype="float32")
        faiss.normalize_L2(embs)

        # crea o carica l'indice e i metadati
        if rebuild or not os.path.exists(self.index_p):
            index = faiss.IndexFlatL2(embs.shape[1])
            meta  = []
        else:
            index = faiss.read_index(self.index_p)
            with open(self.meta_p, "rb") as f:
                meta = pickle.load(f)

        # aggiungi i nuovi vettori e aggiorna i metadati
        index.add(embs)
        meta.extend(new_docs)

        # salva su disco
        faiss.write_index(index, self.index_p)
        with open(self.meta_p, "wb") as f:
            pickle.dump(meta, f)

        # aggiorna il file dei done
        self.done_files.update(os.path.basename(p) for p in to_process)
        with open(self.done_p, "w", encoding="utf-8") as f:
            json.dump(sorted(self.done_files), f, indent=2)

        print(f"✅ Indice aggiornato: +{len(new_docs)} chunk da "
              f"{len(to_process)} file → tot. {len(meta)} vettori.")
