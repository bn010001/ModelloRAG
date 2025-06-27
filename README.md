# ModelloRAG

## 📁 Struttura di progetto

```
/
├ModelloRAG/
├─ config/                         # Configurazioni (YAML/JSON/ENV)
│  └─ params.yaml                  # Parametri RAG per testing
│
├─ data/
│  ├─ index/ 
│  │  ├─ faiss_index.bin
│  │  ├─ indexed_files.json
│  │  └─ metadata.pkl
│  │ 
│  ├─ raw/                         # Documenti di input (immutati)
│  ├─ tmp/                         # File temporanei (OCR, ecc.)
│  └─ processed/                   # Output testuali e immagini
│     ├─ *.txt                     # Testo estratto
│     ├─ images/                   # Immagini estratte dai PDF
│     ├─ image_map.json            # Metadata immagini
│     └─ processed_files.json      # Log dei raw già processati
│
├─ models/                         # Modelli pre-allenati o custom
│  └─ mistral-7b-instruct-v0.1.Q4_K_M.gguf    
│
├─ reports/                        # Test set, benchmark, valutazioni
│  ├─ test_questions.csv           # Domande di prova per RAG
│  └─ test_results.csv             # (es.) output di metriche EM/BLEU/etc.
│
│
├─ requirements.txt                # Python dependencies
│
├─ README.md                       # Documentazione del progetto
│
├─ src/
│  ├─ ingestion/                   # Pipeline di extraction
│  │  ├─ manager.py                # DataProcessor (discover/process/remove…)
│  │  ├─ processors.py             # Txt/Excel/PDF/OCR/ImageProcessor
│  │  └─ pdf_images.py             # Estrattore immagini + captioning
│  │
│  ├─ launcher
│  │  ├─
│  │  └─
│  ├─ rag/                          # RAG core
│  │   ├─ __init__.py
│  │   ├─ indexer.py                # Costruzione e aggiornamento FAISS
│  │   └─ responder.py              # Generazione risposte e logica RAG
│  │
│  ├─ ui/                           # Interfaccia DearPyGui
│  │  ├─ main_ui.py                 # Context, viewport, primary window
│  │  ├─ docs_tab.py                # Tab “Documenti”: ingest & cleanup
│  │  ├─ chat_tab.py                # Tab “Chat”: input/output RAG
│  │  ├─ index_tab.py               # Tab “Index”: visualizza/stato FAISS
│  │  ├─ state.py                   # Stato globale (use_rag, paths…)
│  │  └─ utils.py 
│  │
   └─ rag_tool.py



## Prerequisiti

1. **Sistema operativo**  
   ­– Debian/Ubuntu, macOS, Windows.

2. **Pacchetti di sistema**  
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3-pip tesseract-ocr tesseract-ocr-ita tesseract-ocr-eng \
                    poppler-utils ghostscript

   # macOS (Homebrew)
   brew install tesseract               # include eng; per ita: brew install tesseract-lang
   brew install poppler
   ```

3. **Ambiente Python**  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Modelli LLM** 

   Per usare questo progetto è necessario scaricare manualmente i seguenti modelli `.gguf`:

   - [Mistral-7B-Instruct-v0.1.Q4_K_M.gguf](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF)
     - Dimensione: ~4.2 GB
     - Quantizzazione: Q4_K_M
     - Posiziona il file in `models/`

   Assicurati di scaricare la versione GGUF compatibile con `llama-cpp-python`.




Tutte le librerie sono **open source**; su PyMuPDF licenza AGPL v3 diversa per uso commerciale.

---

## Avvio Interfaccia Grafica

bash
python -m src/ui/main_ui.py
o file di avvio src/launcher/launch.sh o launch.bat

- **Sidebar** per parametri RAG e slider e ridimnsionamento 
- **Tabs**: Chat (RAG), Documenti (DocsTab), Indexing (IndexTab)

---

## DataProcessor (`src/ingestion/manager.py`)

Classe che gestisce:

- `discover_raw()`: elenca i raw in `data/raw/`  
- `get_processed_files()`, `get_unprocessed_files()`: filtri idempotenti  
- `process_all(force=False)`: estrazione testo + immagini + salvataggio  
- `reprocess(fname)`: rielabora un singolo raw esistente  
- `remove(fname)`: rimuove file di output, immagini e record JSON  
- `clear_processed_files()`: “nuke” totale di processed/*.txt, reset JSON  


## Estrazione Testo e OCR (`src/ingestion/processors.py`)

- **TxtProcessor**: lettura pura  
- **ExcelProcessor**: Pandas → CSV  
- **PDFProcessor**: PyMuPDF → `get_text()`  
- **PDFOCRProcessor**:  
  ­– `ocrmypdf` in `tempfile.NamedTemporaryFile` (mai in `data/raw/`)  
  ­– fallback a testo nativo in caso d’errore  
- **ImageProcessor**: OCR Tesseract + caption BLIP (opzionale)

`is_pdf_native()` controlla se usare OCR basato su conteggio caratteri.

---

## Image Captioning (`src/ingestion/pdf_images.py`)

Funzione `extract_pdf_images_with_caption(pdf_path, out_dir)`:
- Estrae immagini interne via PyMuPDF  
- Salva in `data/processed/images/`  
- Per ciascuna immagine:  
  ­– OCR Tesseract (etichette di testo)  
  ­– Caption BLIP (transformers)  
  ­– Rileva diagrammi con CV2 HoughLines  
- Restituisce lista di dict con `source_pdf`, `page`, `image_path`, `is_diagram`, `caption`

---

## GUI Documenti (`ui/docs_tab.py`)

- **Listbox** per file raw/unprocessed  
- **Bottoni** per:  
  ­– Processa nuovi documenti  
  ­– Rielabora selezionato  
  ­– Pulisci tutti i processed  
  ­– Rimuovi duplicati OCR  
- **Status text** aggiornato con `dpg.set_value()`  
- **Utilità**: `threading` per chiamate non‐bloccanti, `flash_status` per messaggi temporanei



_Creazione: Tommaso – Ingegneria Informatica, Università di Perugia_
