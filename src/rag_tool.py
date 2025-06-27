# src/rag_tool.py
import argparse
import csv
import itertools
import os
import time
import yaml

from src.ingestion.manager import DataProcessor
from src.rag.indexer     import RAGIndexer
from src.rag.responder   import RAGResponder

def main():
    parser = argparse.ArgumentParser(prog="ModelloRAG")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ─── ingest ──────────────────────────────
    ingest_p = sub.add_parser("ingest", help="process raw → .txt + image_map.json")
    ingest_p.add_argument("--force", "-f", action="store_true",
                          help="ricalcola tutti i file anziché solo i nuovi")

    # ─── index ───────────────────────────────
    index_p = sub.add_parser("index", help="costruisci o aggiorna l'indice FAISS")
    index_p.add_argument("--rebuild", "-r", action="store_true",
                         help="ricostruisci da zero (default: aggiorna)")

    # ─── query ───────────────────────────────
    query_p = sub.add_parser("query", help="fai QA su domanda")
    query_p.add_argument("--rag", action="store_true",
                         help="uso RAG-retrieval prima di generare")
    query_p.add_argument("--k", type=int, default=5,
                         help="numero di chunk da recuperare (default: 5)")
    query_p.add_argument("question", nargs="+",
                         help="testo della domanda da sottoporre")

    # ─── test ────────────────────────────────
    test_p = sub.add_parser("test", help="esegui test QA su tutte le domande")
    test_p.add_argument("-o", "--output", default="reports/test_results.csv",
                        help="file CSV di risultati")
    test_p.add_argument("-r", "--rebuild-index", action="store_true",
                        help="ricostruisci l’indice prima dei test")

    args = parser.parse_args()

    # ─── INGEST ──────────────────────────────
    if args.cmd == "ingest":
        dp = DataProcessor()
        dp.process_all(force=args.force)

    # ─── INDEX ───────────────────────────────
    elif args.cmd == "index":
        ix = RAGIndexer()
        ix.build(rebuild=args.rebuild)

    # ─── QUERY ───────────────────────────────
    elif args.cmd == "query":
        q = " ".join(args.question)
        rr = RAGResponder(
            model_path="models/mistral-7b-instruct-v0.1.Q4_K_M.gguf",
            index_p="data/processed/faiss_index.bin",
            meta_p="data/processed/metadata.pkl"
        )
        answer = rr.answer(q, with_rag=args.rag, k=args.k)
        print(answer or " Nessuna risposta generata.")

    # ─── TEST ────────────────────────────────
    elif args.cmd == "test":
        print(" Inizio test!")

        # 1) Carica domande
        with open("reports/test_questions.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            tests = list(reader)
        print(f" Domande caricate: {len(tests)}")

        # 2) Carica parametri
        with open("config/params.yaml", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        print(" Parametri caricati:")
        print(f"  chunk_size    = {cfg['chunk_size']}")
        print(f"  chunk_overlap = {cfg['chunk_overlap']}")
        print(f"  k             = {cfg['k']}")
        print(f"  prompt_templates = {[t['name'] for t in cfg['prompt_templates']]}")
        print(f"  temperature   = {cfg['temperature']}")
        print(f"  max_tokens    = {cfg['max_tokens']}")
        print(f"  stop_sequences= {cfg['stop_sequences']}")

        # 3) Prepara CSV di output
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", newline="", encoding="utf-8") as fout:
            writer = csv.writer(fout)
            writer.writerow([
                "id","mode","chunk_size","chunk_overlap","k","template",
                "temperature","max_tokens","stop_sequence",
                "time_retrieval_ms","time_generation_ms",
                "response_token_length","pct_keypoints","response"
            ])

            # 4) Cicla su ogni combinazione
            combos = itertools.product(
                cfg["chunk_size"],
                cfg["chunk_overlap"],
                cfg["k"],
                cfg["prompt_templates"],
                cfg["temperature"],
                cfg["max_tokens"],
                cfg["stop_sequences"]
            )
            for cs, co, k, templ, temp, mt, ss in combos:
                print(f"🔧 Test combo → chunk_size={cs}, chunk_overlap={co}, k={k}, "
                      f"template={templ['name']}, temp={temp}, max_tokens={mt}, stop_seq={ss}")

                # (ri)costruisci l’indice se serve
                if args.rebuild_index:
                    print("   🔄 Ricostruzione indice FAISS…")
                    RAGIndexer(
                        chunk_size=cs,
                        chunk_overlap=co
                    ).build(rebuild=True)

                # Istanzia il responder per questa configurazione
                rr = RAGResponder(
                    model_path="models/mistral-7b-instruct-v0.1.Q4_K_M.gguf",
                    index_p="data/processed/faiss_index.bin",
                    meta_p="data/processed/metadata.pkl",
                    prompt_template=templ["text"],
                    temperature=temp,
                    max_tokens=mt,
                    stop_sequences=[ss]
                )

                for t in tests:
                    qid  = t["id"]
                    qtxt = t["question"]
                    keys = [kp.strip() for kp in t["expected_keypoints"].split(";")]

                    # NO-RAG
                    # t0   = time.time()
                    # resp0 = rr.answer(qtxt, with_rag=False, k=k)
                    # d0   = (time.time() - t0) * 1000

                    # RAG
                    t1   = time.time()
                    resp1 = rr.answer(qtxt, with_rag=True,  k=k)
                    d1   = (time.time() - t1) * 1000

                    def pct_hits(resp, keys):
                        cnt = sum(1 for kp in keys if kp.lower() in resp.lower())
                        return cnt/len(keys)*100 if keys else 0.0

                    # Logga entrambe le modalità
                    for mode, resp, dt in [
                       # ("no-rag", resp0, d0),
                        ("rag",    resp1, d1)
                    ]:
                        writer.writerow([
                            qid, mode, cs, co, k, templ["name"],
                            temp, mt, ss,
                        #    round(d0 if mode=="no-rag" else 0, 2),
                            round(d1 if mode=="rag"    else 0, 2),
                            len(resp.split()),
                            round(pct_hits(resp, keys), 2),
                            resp.replace("\n", " ")
                        ])

        print(f"✅ Test completati. Risultati in {args.output}")

if __name__ == "__main__":
    main()
