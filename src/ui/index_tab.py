# ui/index_tab.py
import threading
import dearpygui.dearpygui as dpg
from ui.state import init_indexer
from ui.utils import flash_status

class IndexTab:
    def __init__(self):
        self.tag_info = "idx_info"

    def setup(self):
        # InputText readonly per mostrare info dinamiche
        dpg.add_input_text(
            tag=self.tag_info,
            default_value="Vettori indicizzati: ",
            readonly=True,
            width=-1
        )
        with dpg.group(horizontal=True):
            dpg.add_button(label="Mostra indice corrente", callback=self.show_current)
            dpg.add_button(label="Ricostruisci Indice", callback=self.rebuild_index)


    def show_current(self, sender, app_data, user_data):
        idx = init_indexer()
        # Provoca una build senza forzare se non è già fatto
        try:
            idx.build(rebuild=False)
        except:
            pass
        
        # Leggi il conteggio FAISS
        faiss_obj = getattr(idx, "faiss_index", None) or getattr(idx, "index", None)
        count = getattr(faiss_obj, "ntotal", "–") if faiss_obj else "–"
        # Mostra nell’InputText
        dpg.set_value(self.tag_info, f" Vettori indicizzati: {count}")
        # Se non c’erano cambi, flash temporaneo
        if count == "–":
            flash_status(self.tag_info, " Nessun file nuovo da indicizzare")


    def rebuild_index(self, sender, app_data, user_data):
        idx = init_indexer()
        def worker():
            idx.build(rebuild=True)
            # Notifica visiva per qualche secondo
            flash_status(
                self.tag_info,
                f" Indice ricostruito: {idx.index.ntotal}"
            )
        threading.Thread(target=worker, daemon=True).start()
