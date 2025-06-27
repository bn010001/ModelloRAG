# ui/docs_tab.py
import os, threading
import dearpygui.dearpygui as dpg
from src.ingestion.manager import DataProcessor
from ui.utils import flash_status

class DocsTab:
    def __init__(self):
        self.dp = DataProcessor()
        self.tag_raw     = "raw_list"
        self.tag_proc    = "proc_list"
        self.tag_status  = "docs_status"

    def setup(self):
        dpg.add_text("Files NON processati:")
        dpg.add_listbox(tag=self.tag_raw, items=[], num_items=6, width=-1)
        dpg.add_text("Files processati:")
        dpg.add_listbox(tag=self.tag_proc, items=[], num_items=6, width=-1)

        # Bottoni azioni
        dpg.add_button(label="Processa nuovi documenti",
                       callback=self._threaded(self._process_all))
        dpg.add_button(label="Rielabora selezionato",
                       callback=self._threaded(self._reprocess_selected))
        dpg.add_button(label="Pulisci tutti i processed",
                       callback=self._threaded(self._clear_all))

        # Etichetta di stato (rimane finché non la sovrascrivi)
        dpg.add_text("", tag=self.tag_status, color=[200,200,0])

        # Popolo subito
        self.refresh_docs()

    def _threaded(self, fn):
        """Restituisce una lambda che esegue fn() in background."""
        return lambda s,a,u: threading.Thread(target=fn, daemon=True).start()

    # ── Operazioni ────────────────────────────────────
    def _process_all(self):
        dpg.set_value(self.tag_status, " Processamento in corso…")
        try:
            self.dp.process_all(force=False)
            self.refresh_docs()
            dpg.set_value(self.tag_status, " Processamento completato")
        except Exception as e:
            dpg.set_value(self.tag_status, f" Errore: {e}")

    def _reprocess_selected(self):
        # prendo selezione da processed; se vuoto chiedo all’utente
        fname = dpg.get_value(self.tag_proc)
        if not fname:
            flash_status(self.tag_status, "Seleziona un file da rielaborare", 2.0)
            return

        dpg.set_value(self.tag_status, f" Rielaboro {fname}…")
        try:
            self.dp.reprocess(fname)
            self.refresh_docs()
            dpg.set_value(self.tag_status, f" Rielaborazione di {fname} completata")
        except Exception as e:
            dpg.set_value(self.tag_status, f" Errore: {e}")

    def _clear_all(self):
        dpg.set_value(self.tag_status, " Pulizia dei processed in corso…")
        try:
            self.dp.clear_processed_files()
            self.refresh_docs()
            dpg.set_value(self.tag_status, " Tutti i processed sono stati cancellati")
        except Exception as e:
            dpg.set_value(self.tag_status, f" Errore: {e}")

    def _remove_ocr(self):
        dpg.set_value(self.tag_status, " Rimozione duplicati OCR…")
        raw = self.dp.raw_dir
        removed = 0
        for f in os.listdir(raw):
            if f.lower().endswith(".pdf") and "_ocr" in f.lower():
                try:
                    os.remove(os.path.join(raw,f))
                except:
                    pass
                self.dp.remove(f)
                removed += 1
        self.refresh_docs()
        dpg.set_value(self.tag_status, f" Rimossi {removed} duplicati OCR")

    # ── Utility ──────────────────────────────────────
    def refresh_docs(self):
        dpg.configure_item(self.tag_raw,  items=self.dp.get_unprocessed_files())
        dpg.configure_item(self.tag_proc, items=self.dp.get_processed_files())
