# ui/chat_tab.py

import threading
import dearpygui.dearpygui as dpg
from ui.state    import init_responder, state
from ui.utils    import append_chat

class ChatTab:
    def __init__(self):
        self.tag_input  = "chat_input"
        self.tag_status = "chat_status"
        self.tag_log    = "chat_log"

    def setup(self):
        # ── Input multiline + button affiancato ───────────
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag=self.tag_input,
                hint="Scrivi la tua domanda qui…",
                multiline=True,
                no_horizontal_scroll=True,
                height=80,
                width=-1,
                on_enter=True,
                callback=self.chat_callback
            )
            dpg.add_separator()
        dpg.add_button(label="Invia", width=80, callback=self.chat_callback)

        dpg.add_separator()

        # ── Status (wrap) ──────────────────────────────────
        dpg.add_text("", tag=self.tag_status, wrap=600)

        # ── Registro chat multiline ─────────────────────────
        dpg.add_spacer(height=10)
        dpg.add_text("Registro Chat:")
        dpg.add_input_text(
            tag=self.tag_log,
            multiline=True,
            readonly=True,
            no_horizontal_scroll=True,
            height=300,
            width=-1
        )

    def chat_callback(self, sender, app_data, user_data):
        question = dpg.get_value(self.tag_input).strip()
        if not question:
            return

        append_chat(f" Tu: {question}")
        dpg.set_value(self.tag_input, "")
        dpg.set_value(self.tag_status, "Sto generando…")

        use_rag = state["use_rag"]
        responder = init_responder()

        def worker():
            # sincronizziamo le chiamate al LLM per evitare segfault
            with state["lock"]:
                answer = responder.answer(
                    question,
                    with_rag=use_rag,
                    k=state["k"]
                )
            print(f"\n Risposta (RAG={use_rag}):\n{answer}\n---")
            append_chat(f"Bot: {answer}")
            dpg.set_value(self.tag_status, "")

        threading.Thread(target=worker, daemon=True).start()
