import threading
import dearpygui.dearpygui as dpg

def append_chat(text):
    """Accoda una riga al log della chat"""
    log = dpg.get_value("chat_log")
    dpg.set_value("chat_log", log + text + "\n")

def flash_status(tag, message, duration=2.0):
    """Mostra un messaggio temporaneo in widget `tag`"""
    dpg.set_value(tag, message)
    threading.Timer(duration, lambda: dpg.set_value(tag, "")).start()
