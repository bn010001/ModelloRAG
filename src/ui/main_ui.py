# ui/main_ui.py

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import dearpygui.dearpygui as dpg
from ui.state     import state, init_indexer
from ui.chat_tab  import ChatTab
from ui.docs_tab  import DocsTab
from ui.index_tab import IndexTab

def main():
    # ── Context e Viewport ────────────────────────────────
    dpg.create_context()
    dpg.create_viewport(title="RAG", width=1100, height=700)

    # ── Finestra invisibile che fa da root ───────────────
    with dpg.window(
        tag="main_panel",      # ← tag per set_primary_window
        label="",              # niente title bar
        pos=(0, 0),
        width=dpg.get_viewport_client_width(),
        height=dpg.get_viewport_client_height(),
        no_title_bar=True,
        no_resize=True,
        no_move=True,
        no_close=True
    ):
        # Sidebar + area tab affiancate
        with dpg.group(horizontal=True):

            # ── Sidebar ───────────────────────────────────
            with dpg.child_window(
                tag="sidebar_container",
                width=250, height=-1,
                border=True
            ):

                dpg.add_text("Larghezza Sidebar")
                dpg.add_slider_int(
                    tag="sidebar_width",
                    default_value=250,
                    min_value=100, max_value=600,
                    callback=lambda sender, value, user_data: dpg.configure_item("sidebar_container", width=value)
                )

                dpg.add_spacer(height=10)
                dpg.add_text("PARAMETRI RAG")
                dpg.add_text("Modalità:")
                dpg.add_radio_button(
                    items=["RAG","No RAG"],
                    tag="mode_selector",
                    default_value="RAG" if state["use_rag"] else "NoRAG",
                    horizontal=True,
                    callback=lambda sender, value, user_data: state.update({"use_rag": value=="RAG"})
                )

                dpg.add_spacer(height=10)
                dpg.add_slider_int(
                    tag="k", label="Chunks k", width=-1,
                    default_value=state["k"], min_value=1, max_value=20,
                    callback=lambda sender, value, user_data: state.update({"k": value})
                )
                dpg.add_slider_float(
                    tag="temperature", label="Temperature", width=-1,
                    default_value=state["temperature"], min_value=0.0, max_value=1.0,
                    callback=lambda sender, value, user_data: state.update({"temperature": value})
                )
                dpg.add_slider_int(
                    tag="max_tokens", label="Max tokens", width=-1,
                    default_value=state["max_tokens"], min_value=16, max_value=2048,
                    callback=lambda sender, value, user_data: state.update({"max_tokens": value})
                )
                dpg.add_combo(
                    items=["\n\n","Fine risp."],
                    tag="stop_sequence", label="Stop sequence", width=-1,
                    default_value=state["stop_sequence"],
                    callback=lambda sender, value, user_data: state.update({"stop_sequence": value})
                )
                dpg.add_combo(
                    items=["base","cite"],
                    tag="prompt_template", label="Prompt template", width=-1,
                    default_value="base",
                    callback=lambda sender, value, user_data: state.update({
                        "prompt_template":
                            ("Contesto:\n{context}\n\nDomanda: {query}\nRisposta:"
                             if value=="base"
                             else
                             "Usa solo le informazioni seguenti...\n{context}\n\nDomanda: {query}\nRisposta (specifica e documentata):")
                    })
                )

                dpg.add_spacer(height=20)
                dpg.add_text("PARAMETRI INDEX")
                dpg.add_slider_int(
                    tag="chunk_size", label="Chunk size", width=-1,
                    default_value=state["chunk_size"], min_value=100, max_value=2000,
                    callback=lambda sender, value, user_data: state.update({"chunk_size": value})
                )
                dpg.add_slider_int(
                    tag="chunk_overlap", label="Chunk overlap", width=-1,
                    default_value=state["chunk_overlap"], min_value=0, max_value=500,
                    callback=lambda sender, value, user_data: state.update({"chunk_overlap": value})
                )
                dpg.add_button(
                    label="Ricostruisci Indice", width=-1,
                    callback=lambda sender, app_data, user_data: IndexTab().rebuild_index(sender, app_data, user_data)
                )

            # ── Area principale ─────────────────────────────
            with dpg.child_window(
                tag="main_area",
                width=-1, height=-1,
                border=False
            ):
                with dpg.tab_bar():
                    with dpg.tab(label=" Chat"):
                        ChatTab().setup()
                    with dpg.tab(label=" Documenti"):
                        DocsTab().setup()
                    with dpg.tab(label=" Indexing"):
                        IndexTab().setup()

    # ── Indica a DPG che main_panel è la finestra primaria ─
    dpg.set_primary_window("main_panel", True)

    # Inizializza index e popola docs all’avvio
    init_indexer()
    DocsTab().refresh_docs()

    # ── Avvio ─────────────────────────────────────────────
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
