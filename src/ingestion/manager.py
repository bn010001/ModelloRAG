# src/ingestion/manager.py
import os, json, logging
from glob import glob
from src.ingestion.processors import process_file
from src.ingestion.pdf_images import extract_pdf_images_with_caption

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DataProcessor:
    def __init__(
        self,
        raw_dir="data/raw",
        processed_dir="data/processed",
        image_map_path="data/processed/image_map.json",
        record_path="data/processed/processed_files.json"
    ):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.image_map_path = image_map_path
        self.record_path = record_path

        os.makedirs(self.processed_dir, exist_ok=True)
        # carica record dei file già processati
        if os.path.exists(self.record_path):
            self.processed_files = set(json.load(open(self.record_path)))
        else:
            self.processed_files = set()

        # carica mappa immagini esistente
        if os.path.exists(self.image_map_path):
            self.image_map = json.load(open(self.image_map_path))
        else:
            self.image_map = []

    def save_state(self):
        # salva record dei raw processati
        with open(self.record_path, "w", encoding="utf-8") as f:
            json.dump(list(self.processed_files), f, indent=2)
        # salva mappa immagini aggregata
        with open(self.image_map_path, "w", encoding="utf-8") as f:
            json.dump(self.image_map, f, indent=2, ensure_ascii=False)

    def discover_raw(self):
        exts = (".pdf", ".txt", ".jpg", ".jpeg", ".png", ".xlsx")
        return [
            p for p in glob(os.path.join(self.raw_dir, "*"))
            if p.lower().endswith(exts)
        ]

    def process_all(self, force=False):
        """
        Elabora tutti i raw, salva .txt in processed_dir e aggiorna image_map.
        Se force=True, rielabora anche quelli già processati.
        """
        raws = self.discover_raw()
        for path in raws:
            fname = os.path.basename(path)
            if not force and fname in self.processed_files:
                continue

            logger.info(f"→ Processing {fname}")
            try:
                text = process_file(path)
            except Exception as e:
                logger.warning(f"  ✗ fallito estrazione di {fname}: {e}")
                continue

            # salva .txt
            base = os.path.splitext(fname)[0]
            out_txt = os.path.join(self.processed_dir, base + ".txt")
            with open(out_txt, "w", encoding="utf-8") as f:
                f.write(text)

            # se è PDF, estrai immagini + caption
            if fname.lower().endswith(".pdf"):
                new_captions = extract_pdf_images_with_caption(path)
                self.image_map.extend(new_captions)

            self.processed_files.add(fname)

        # una volta finito, salva lo stato
        self.save_state()
        logger.info(f"✅ Processing completato. Totali file raw processati: {len(self.processed_files)}")

    def get_processed_files(self) -> list[str]:
        """
        Ritorna la lista dei nomi dei file raw già processati.
        """
        return sorted(self.processed_files)

    def get_unprocessed_files(self) -> list[str]:
        """
        Ritorna la lista dei nomi dei file raw ancora da processare.
        """
        all_raws = [os.path.basename(p) for p in self.discover_raw()]
        return sorted([f for f in all_raws if f not in self.processed_files])
    
    def clear_processed_files(self):
        """
        Elimina tutti i .txt processati, resetta processed_files e image_map.
        Aggiorna i log in modo sicuro e logga quanti elementi sono stati rimossi.
        """
        try:
            # 1. Rimuovi tutti i .txt
            txt_files = glob(os.path.join(self.processed_dir, "*.txt"))
            for f in txt_files:
                try:
                    os.remove(f)
                    logger.info(f"🗑️  Rimosso: {f}")
                except Exception as e:
                    logger.warning(f"⚠️ Errore nella rimozione di {f}: {e}")
    
            # 2. Conta e azzera i record
            num_processed = len(self.processed_files)
            num_images    = len(self.image_map)
    
            self.processed_files.clear()
            self.image_map.clear()
    
            # 3. Salva i nuovi log vuoti
            self.save_state()
    
            logger.info(f"✅ Eliminati {num_processed} file dal registro processed_files.")
            logger.info(f"✅ Rimossa image_map con {num_images} immagini collegate.")
            logger.info("🧼 Pulizia completata con successo.")
    
        except Exception as e:
            logger.exception(f"❌ Errore critico durante clear_processed_files: {e}")


    def remove(self, fname: str):
        """
        Rimuove tutto ciò che è associato a un raw file:
        - il file .txt processato
        - le immagini in image_map
        - l’entry nel record dei file processati (se presente)
        Anche se il raw non esiste più.
        """
        try:
            base = os.path.splitext(fname)[0]

            # 1. Elimina .txt generato
            txt_path = os.path.join(self.processed_dir, base + ".txt")
            if os.path.exists(txt_path):
                os.remove(txt_path)
                logger.info(f"🗑️  Rimosso file di testo: {txt_path}")
            else:
                logger.debug(f"– Nessun .txt da rimuovere per {fname}")

            # 2. Pulisci image_map (anche se non nel record)
            prima = len(self.image_map)
            self.image_map = [
                im for im in self.image_map
                if im.get("source_pdf") != fname
            ]
            rimossi = prima - len(self.image_map)
            if rimossi:
                logger.info(f"🧹 Rimosse {rimossi} immagini collegate a {fname}")
            else:
                logger.debug(f"– Nessuna immagine collegata a {fname} in image_map")

            # 3. Rimuovi dal record processati
            if fname in self.processed_files:
                self.processed_files.remove(fname)
                logger.info(f"🗂️  File rimosso dal registro: {fname}")
            else:
                logger.debug(f"– {fname} non era nel registro processed_files")

            # 4. Salva stato aggiornato
            self.save_state()

        except Exception as e:
            logger.warning(f"⚠️ Errore durante la rimozione di {fname}: {e}")
